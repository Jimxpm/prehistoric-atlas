# 圖片素材紀錄

2026-11-15：四張使用者提供的 PNG 均保留；網站採 WebP。未重新生成、下載或修改畫面內容。

| 原始檔／網站素材（相同主檔名） | 尺寸 | PNG → WebP 大小（bytes） | 用途 |
| --- | --- | --- | --- |
| cambrian-ocean-hero.png / .webp | 1672×941 | 2,699,068 → 262,160 | 首頁 Hero |
| anomalocaris-canadensis-hero.png / .webp | 1672×941 | 2,426,406 → 226,642 | 奇蝦 Hero／卡片 |
| opabinia-regalis-hero.png / .webp | 1672×941 | 2,536,344 → 252,582 | 歐巴賓海蠍 Hero／卡片 |
| dunkleosteus-terrelli-hero.png / .webp | 1671×941 | 2,522,046 → 254,686 | 鄧氏魚 Hero／卡片 |

轉換：Pillow 12.2.0，RGB、WebP quality=85、method=6；不縮放、不裁切、不放大。圖片解碼與瀏覽器載入均已檢查。共用 CSS 使用 contain 維持比例；桌面物種主圖靠右，手機圖片在文字上方。

首頁設定在 data/site.json；物種 Hero 與卡片共用 data/species/<species-id>.json 的 image 和 image_metadata，type 均為 ai。頁面標示「AI 生成藝術復原圖 · 非化石證據」，說明形態與生態細節含藝術想像，不宣稱經科學解剖校訂。

來源：使用者提供供本專案使用。生成工具、模型、提示詞及額外再授權條款未提供，不臆造作者或開放授權。

目前沒有缺少的必要圖片。日後替換圖片時保留 PNG，產生 <species-id>-hero.webp，更新 JSON 後重新建置；缺圖則使用 null 與 placeholder，列出檔名、建議 16:9 與構圖要求。圖片來源與揭露不可省略。
