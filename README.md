# Prehistoric Atlas｜史前生命圖鑑

繁體中文數位自然史展覽。目前包含首頁及奇蝦、歐巴賓海蠍、鄧氏魚三個介紹頁；本地擴充與圖片整合已完成。請以此目錄作為專案根目錄，無須建立額外子專案。長期規則見 AGENTS.md。

## 建置與預覽

需要 Python 3.9 以上，無第三方套件、API 金鑰、後端或資料庫。

```powershell
python scripts/build.py
python -m unittest discover -s tests -v
python -m http.server 8000 --bind 127.0.0.1
```

開啟 http://127.0.0.1:8000/ ，或直接以瀏覽器開啟 index.html。停止伺服器按 Ctrl+C。生成器可由任意工作目錄以絕對路徑執行。網站本身不需要 Python，不使用 JavaScript：現有導覽與章節跳轉均由原生 HTML 完成。

## 目錄與資料流

- `data/species/*.json`：物種知識的唯一主要來源；首頁卡片與物種頁共用。
- `data/site.json`：首頁圖片設定。
- `templates/base.html`：共用頁首、頁尾、語言與資源引用。
- `templates/home.html`、`species.html`、`card.html`：共用首頁、物種頁與卡片模板。
- `scripts/build.py`：標準函式庫 JSON 驗證、HTML 跳脫、模板生成與站內連結／錨點檢查。
- `assets/css/style.css`：集中色票、響應式排版、焦點與 reduced-motion 設定。
- `assets/images/README.md`：圖片來源、轉換紀錄與素材規範。
- `tests/test_build.py`：使用暫存資料驗證建置與失敗情境，不污染正式資料。
- `index.html`、`pages/*.html`：生成成品，請勿直接編輯。

所有頁面在寫入前完成資料與連結檢查；失敗回傳非零退出碼。生成器不刪除既有頁面：若頁面已無對應 JSON，會警告供人工確認，避免擅自刪除。模板採 Python string.Template，只將生成器產生的 HTML 片段直接插入；資料文字一律跳脫。

## JSON 格式（第一版）

可直接以 `data/species/anomalocaris-canadensis.json` 為真實範例。

| 欄位 | 格式 |
| --- | --- |
| id | 小寫學名 slug；須等於 JSON 檔名（不含副檔名），不可重複 |
| name_zh、scientific_name | 非空文字 |
| period | 統一使用非空字串，包含繁中與英文地質年代 |
| habitat、diet、size、summary | 非空文字；不確定性直接寫入描述 |
| features | 至少一項的文字陣列 |
| story | 至少一段；每段含 title、kind、text 非空文字及 source_refs 來源序號陣列（從 1 起） |
| image | 缺圖為 null；有圖為 assets/images/ 下專案相對路徑，支援 webp/png/jpg/jpeg |
| image_metadata | 必填 type、description、author、license；皆為非空文字 |
| sources | 非空陣列，每筆含 title、organization_or_author、url（HTTP/S）、accessed_date（YYYY-MM-DD） |
| uncertainty_notes | 可選文字陣列，補充科學限制；省略時顯示共用提醒 |

image_metadata.type 只能為 placeholder、ai、licensed。null 圖片必須使用 placeholder；有圖必須使用 ai 或 licensed，檔案必須存在。description 記錄生成說明或素材來源 URL；author 與 license 記錄作者及使用條件。AI 圖為藝術復原，不是化石證據。這份格式亦適用於 data/site.json 的 image 與 image_metadata。

## 科學來源與限制

2026-11-15 實際讀取皇家安大略博物館奇蝦頁，以及 Bicknell 等人 2023 年研究在 PubMed 的摘要與書目資料：

- https://burgess-shale.rom.on.ca/fossils/anomalocaris-canadensis/
- https://pubmed.ncbi.nlm.nih.gov/37403497/

形態、地層、標本與體型推估參考前者；食性功能研究參考後者（DOI: 10.1098/rspb.2023.0638）。PMC 全文入口遇到驗證頁，未聲稱已審閱全文或補充模型資料。體型保留「完整標本約 25 公分」與「零散標本外推可能達約 1 公尺」的差別，不將外推當作實測。科學知識仍可能隨研究更新，頁面以 [1]、[2] 與段落來源連結追溯。

## 圖片已整合

四張使用者提供的 AI 生成藝術復原圖皆已有 WebP，原始 PNG 保留。首頁 Hero、三個物種 Hero 與卡片均使用本地 WebP，圖片不是化石證據。

| 檔案（assets/images/） | 尺寸 | 大小 | 用途 |
| --- | --- | --- | --- |
| cambrian-ocean-hero.webp | 1672×941 | 262,160 bytes | 首頁 Hero |
| anomalocaris-canadensis-hero.webp | 1672×941 | 226,642 bytes | 奇蝦 Hero 與首頁卡片 |
| opabinia-regalis-hero.webp | 1672×941 | 252,582 bytes | 歐巴賓海蠍 Hero 與首頁卡片 |
| dunkleosteus-terrelli-hero.webp | 1671×941 | 254,686 bytes | 鄧氏魚 Hero 與首頁卡片 |

採 Pillow 12.2.0，RGB、WebP quality=85、method=6，保留原尺寸、不放大。Pillow 僅用於這次素材轉換，日常建置仍無第三方依賴。重做轉換可用 `Image.open(png).convert("RGB").save(webp, "WEBP", quality=85, method=6)`。

來源、生成工具未知狀態與使用條款紀錄於既有 JSON image_metadata；詳細說明見 assets/images/README.md。桌面沿用深色遮罩，物種 Hero 圖片採右側 contain 並微調長標題大小，手機完整呈現橫幅於 Hero 上方，文字接續下方；卡片以 contain 保持主體完整、不變形。未改動科學內容。未來物種缺圖時仍可使用 null 與共用 CSS 暫代機制。

## 後續新增物種流程

1. 依 AGENTS.md，先讀 README、現有 JSON 與模板。
2. 查核博物館／研究機構／論文，保留爭議與查閱日期。
3. 新增 `data/species/<scientific-name>.json`，遵循上述相同格式。
4. 提供有來源的圖片或設 image 為 null 並標示 placeholder。
5. 執行建置與測試；首頁卡片、物種頁、其他物種導覽會自動加入，無須手動維護首頁。
6. 檢視桌面、手機、資料來源與圖片揭露，整理未完成項目。

測試中的 fixture-species 僅為暫存資料，不是正式物種；正式資料只有上述三種。現有 14 項測試包含動態物種數、互連、有圖／缺圖混合、資料錯誤與重複建置一致性。

## 純靜態與子路徑相容性

所有站內資源使用相對路徑，離線測試驗證 /repository-name/ 子路徑解析。無外部字型、CDN 或執行期依賴。現正進行公開部署前檢查；實際發布結果以 VALIDATION.md 最新紀錄為準。

## 本次驗收

已執行的測試、瀏覽器檢視與尚未驗證項目，詳見 [VALIDATION.md](VALIDATION.md)。

## 歐巴賓海蠍擴充（2026-11-15）

新增 data/species/opabinia-regalis.json，沿用全部既有欄位、模板、CSS 與生成器。首頁與物種間導覽自動更新。既有奇蝦 JSON 位元組未變更；奇蝦 HTML 僅由建置更新其他物種導覽。

資料查閱來源：
- https://burgess-shale.rom.on.ca/fossils/opabinia-regalis/ （博物館形態、尺寸、地層與生態解釋）
- https://discovery.ucl.ac.uk/id/eprint/10208441/ （Pates 等人 2022 年研究摘要與書目，DOI 10.1098/rspb.2021.2093；未聲稱重做系統發育分析或審查全文）

歐巴賓海蠍圖片已整合；此次僅更新其 image 與 image_metadata，科學內容未變更。奇蝦 JSON 維持原樣。

## 鄧氏魚擴充與本地完成（2026-11-15）

新增 data/species/dunkleosteus-terrelli.json，保留體長估算、食性與全身復原的限制。實際讀取以下論文網頁的摘要與引言／相關文字，並核對書目；未聲稱逐項審查完整方法、補充資料或重做模型：

- [Engelman 2023：體長估算](https://www.mdpi.com/1424-2818/15/3/318)
- [Engelman 2024：身體復原](https://www.palaeo-electronica.org/content/2024/5307-dunkleosteus-reconstruction)
- [Engelman 等人：顎部與食性功能](https://anatomypubs.onlinelibrary.wiley.com/doi/10.1002/ar.70075)（2025 線上發表，2026 卷期）

生成器與資料架構無須修改；三個物種重用同一模板，自動產生首頁卡片與互相導覽。僅微調共用 CSS，避免長名稱遮住圖片主體，並更新 base.html 的 CSS 版本查詢參數，避免舊快取影響檢視。AGENTS.md 已補入動態測試、有圖／缺圖狀態、長名稱、來源與轉檔規則。

完整本地驗收見 VALIDATION.md；SUBMISSION_DRAFT.md 為尚未提交的繁體中文作業草稿。所有必要圖片已齊全，生成工具與額外再授權條款仍未提供；藝術圖未經科學形態校訂。實體手機、多瀏覽器與完整無障礙稽核未執行。

## GitHub Pages 發布方式

採用分支發布：main 分支的根目錄（/），直接發布已生成的 index.html、pages/ 與 assets/。根目錄 .nojekyll 停用 Jekyll 處理；更新資料後先執行建置與測試，再提交生成成品。

.gitignore 排除快取、虛擬環境、暫存檔、憑證與原始 PNG。PNG 僅保留於本地；公開儲存庫提供四張 WebP、完整 JSON、模板、生成器、測試與作業文件。
