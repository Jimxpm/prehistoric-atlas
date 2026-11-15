"""Dependency-free static site builder. Run from any working directory."""
import json
import re
import sys
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from string import Template
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
TEXT_FIELDS = ("id", "name_zh", "scientific_name", "period", "habitat", "diet", "size", "summary")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: JSON 讀取失敗: {exc}") from exc


def validate_image(data, root):
    require("image" in data, "缺少 image 欄位；缺圖請填 null")
    meta = data.get("image_metadata")
    require(isinstance(meta, dict), "image_metadata 必須是物件")
    require(meta.get("type") in ("placeholder", "ai", "licensed"), "圖片類型必須是 placeholder / ai / licensed")
    for field in ("description", "author", "license"):
        require(nonempty(meta.get(field)), f"image_metadata.{field} 必須為非空文字")
    value = data["image"]
    if value is None:
        require(meta["type"] == "placeholder", "缺圖必須標為 placeholder")
        return
    require(nonempty(value), "image 必須為相對路徑或 null")
    require(bool(re.fullmatch(r"assets/images/[a-z0-9]+(?:-[a-z0-9]+)*\.(?:webp|png|jpg|jpeg)", value)), "圖片需位於 assets/images/ 並使用小寫連字號檔名")
    require((root / value).resolve().is_relative_to(root.resolve()), "圖片路徑不可離開專案")
    require((root / value).is_file(), f"圖片不存在: {value}")
    require(meta["type"] != "placeholder", "已有圖片須填寫 ai 或 licensed 及來源說明")


def validate_species(data, filename, root):
    require(isinstance(data, dict), "物種 JSON 必須為物件")
    for field in TEXT_FIELDS:
        require(nonempty(data.get(field)), f"{field} 必須為非空文字")
    require(bool(re.fullmatch(r"[a-z]+(?:-[a-z]+)+", data["id"])), "id 必須是小寫學名 slug")
    require(filename == data["id"] + ".json", "檔名必須與 id 相同")
    for field in ("features", "uncertainty_notes"):
        values = data.get(field, [] if field == "uncertainty_notes" else None)
        require(isinstance(values, list) and (field != "features" or bool(values)), f"{field} 必須是列表")
        require(all(nonempty(v) for v in values), f"{field} 每項必須為非空文字")
    sources = data.get("sources")
    require(isinstance(sources, list) and bool(sources), "sources 必須是非空列表")
    for source in sources:
        require(isinstance(source, dict), "來源必須是物件")
        for field in ("title", "organization_or_author", "url", "accessed_date"):
            require(nonempty(source.get(field)), f"來源缺少 {field}")
        url = urlsplit(source["url"])
        require(url.scheme in ("http", "https") and bool(url.netloc), "來源 URL 必須是 HTTP(S)")
        date.fromisoformat(source["accessed_date"])
    story = data.get("story")
    require(isinstance(story, list) and bool(story), "story 必須是非空列表")
    for part in story:
        require(isinstance(part, dict), "story 段落必須是物件")
        for field in ("title", "kind", "text"):
            require(nonempty(part.get(field)), f"story 缺少 {field}")
        refs = part.get("source_refs")
        require(isinstance(refs, list) and bool(refs), "story 需有 source_refs")
        require(all(type(i) is int and 1 <= i <= len(sources) for i in refs), "source_refs 索引超出來源列表")
    validate_image(data, root)


def load_species(root):
    result, seen = [], set()
    for path in sorted((root / "data/species").glob("*.json")):
        data = read_json(path)
        try:
            require(isinstance(data, dict), "物種 JSON 必須為物件")
            require(data.get("id") not in seen, f"重複 id: {data.get('id')}")
            validate_species(data, path.name, root)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{path.name}: {exc}") from exc
        seen.add(data["id"])
        result.append(data)
    require(bool(result), "data/species/ 沒有物種 JSON")
    return result


def render(root, name, **values):
    return Template((root / "templates" / name).read_text(encoding="utf-8")).substitute(values)


def e(value):
    return escape(str(value), quote=True)


def media(data, prefix, alt):
    if data["image"] is None:
        return '<div class="media placeholder" aria-hidden="true"></div>'
    return f'<img class="media" src="{prefix}{e(data["image"])}" alt="{e(alt)}">'


def label(data):
    return {"placeholder": "暫代光影 · 復原圖待提供", "ai": "AI 生成藝術復原圖 · 非化石證據", "licensed": "授權圖片 · 詳見圖片說明"}[data["image_metadata"]["type"]]


def disclosure(data):
    m = data["image_metadata"]
    return e(f'{label(data)}。{m["description"]} 作者：{m["author"]}；授權：{m["license"]}')


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links, self.ids = [], set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            require(a["id"] not in self.ids, f"重複 HTML id: {a['id']}")
            self.ids.add(a["id"])
        if tag == "img":
            require(nonempty(a.get("alt")), "圖片缺少 alt")
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])


def check_links(root, outputs):
    docs = {path.resolve(): Document(html) for path, html in outputs.items()}
    for path, doc in docs.items():
        for link in doc.links:
            url = urlsplit(link)
            if url.scheme in ("http", "https"):
                continue
            require(not url.scheme and not url.netloc and not link.startswith("/"), f"非相對站內連結: {link}")
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            require(target.is_relative_to(root.resolve()), f"連結超出專案: {link}")
            require(target in docs or target.is_file(), f"失效站內路徑: {path.name} -> {link}")
            if url.fragment:
                target_doc = docs.get(target)
                if target_doc is None and target.suffix == ".html":
                    target_doc = Document(target.read_text(encoding="utf-8"))
                require(target_doc is not None and unquote(url.fragment) in target_doc.ids, f"失效錨點: {link}")


def build(root=ROOT):
    root = Path(root)
    species = load_species(root)
    site = read_json(root / "data/site.json")
    require(isinstance(site, dict), "site.json 必須是物件")
    validate_image(site, root)
    outputs, cards = {}, []
    for s in species:
        common = {k: e(s[k]) for k in TEXT_FIELDS}
        cards.append(render(root, "card.html", **common, media=media(s, "", s["name_zh"] + "環境藝術復原"), disclosure=label(s)))
        facts = "".join(f'<div><dt>{title}</dt><dd>{e(s[key])}</dd></div>' for title, key in (("年代", "period"), ("棲地", "habitat"), ("食性", "diet"), ("體型", "size")))
        stories = []
        for part in s["story"]:
            refs = " ".join(f'<a href="#source-{i}">[{i}]</a>' for i in part["source_refs"])
            stories.append(f'<article class="story"><p class="eyebrow">{e(part["kind"])}</p><div><h3>{e(part["title"])}</h3><p>{e(part["text"])}</p>{refs}</div></article>')
        sources = "".join(f'<li id="source-{i}"><a href="{e(source["url"])}">{e(source["title"])}</a><small>{e(source["organization_or_author"])} · 查閱：{e(source["accessed_date"])}</small></li>' for i, source in enumerate(s["sources"], 1))
        other = "".join(f'<a href="{e(o["id"])}.html">探索 {e(o["name_zh"])} →</a>' for o in species if o["id"] != s["id"])
        content = render(root, "species.html", **common, media=media(s, "../", s["name_zh"] + "環境藝術復原"), disclosure=label(s), facts=facts, features="".join(f"<li>{e(v)}</li>" for v in s["features"]), story="".join(stories), sources=sources, source_count=len(s["sources"]), uncertainties="".join(f"<li>{e(v)}</li>" for v in s.get("uncertainty_notes", [])) or "<li>目前未另列補充項目；請留意內文中的推論標示。</li>", image_disclosure=disclosure(s), other_species=other)
        outputs[root / "pages" / (s["id"] + ".html")] = render(root, "base.html", title=e(s["name_zh"]), description=e(s["summary"]), prefix="../", content=content)
    content = render(root, "home.html", media=media(site, "", "寒武紀海洋生態環境藝術復原"), disclosure=label(site), image_disclosure=disclosure(site), count=len(species), cards="".join(cards))
    outputs[root / "index.html"] = render(root, "base.html", title="探索遠古海洋", description="以可追溯的科學資料，探索史前生命與古海世界。", prefix="", content=content)
    check_links(root, outputs)
    for path, html in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    stale = set((root / "pages").glob("*.html")) - set(outputs)
    if stale:
        print("WARNING: 未刪除不在資料中的既有頁面: " + ", ".join(p.name for p in stale))
    missing = sum(s["image"] is None for s in [site, *species])
    print(f"OK: {len(species)} species, {len(outputs)} pages; links checked; {missing} image placeholders")
    return outputs


if __name__ == "__main__":
    try:
        build()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
