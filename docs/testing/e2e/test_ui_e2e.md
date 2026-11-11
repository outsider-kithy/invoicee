# UI E2Eテスト仕様書 — `test_ui_e2e.py`

## 1. 概要

Flaskアプリケーション **invoicee** のPCブラウザ向けUIを、pytestとPlaywrightで検証する。対象は主にログイン後の `/top/` 画面と、共通テンプレート `top/base.html` によるナビゲーションおよび静的リソース。レスポンシブ表示・モバイル画面は対象外とする。

- **テストファイル**：`tests/e2e/test_ui_e2e.py`
- **テスト件数**：15件（UI-E2E-001〜015）
- **実行結果**：15件すべてPASS（ユーザー確認済み）
- **Viewport**：1440 × 900 px
- **使用技術**：Python、pytest、Playwright（Chromiumを想定）、Flask
- **既存fixture**：`auth_page`、`page`、`e2e_server`
- **DBへの変更**：テスト本体では登録・更新・削除を行わない

## 2. テスト対象

### 2.1 画面・テンプレート

| 対象 | 役割 |
|---|---|
| `/top/` | ログイン後のトップページ・ジョブ一覧 |
| `/login/` | 未認証時のナビゲーション確認 |
| `/estimate/` | メニューからの遷移先確認 |
| `top/templates/top/base.html` | HTMLメタ情報、共通ナビゲーション、ロゴ、CSS・JS |
| `top/templates/top/index.html` | 見出し、ジョブ一覧テーブル、見積状態、未見積合計 |

### 2.2 共通テスト条件

`open_top(page, base_url)` ヘルパーでViewportを `1440 × 900` に設定し、`/top/` へ遷移してHTTP 200を確認する。認証が必要なテストでは `auth_page` を使用する。

## 3. テストケース一覧

| ID | pytest関数 | 検証内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| UI-E2E-001 | `test_ui_001_top_display` | トップページの表示 | `/top/` がHTTP 200で、見出し「トップページ」が可視 | PASS |
| UI-E2E-002 | `test_ui_002_title` | ページタイトル | `トップページ - invoicee` と一致 | PASS |
| UI-E2E-003 | `test_ui_003_html_metadata` | HTMLメタ情報 | `lang="ja"`、UTF-8、`robots=noindex,nofollow` | PASS |
| UI-E2E-004 | `test_ui_004_logo` | ロゴ画像とリンク | ロゴが可視、`alt="invoicee"`、画像読み込み成功、リンク先 `/top/` | PASS |
| UI-E2E-005 | `test_ui_005_authenticated_menu` | 認証済みメニュー | 7件の項目と表示順が期待値どおり | PASS |
| UI-E2E-006 | `test_ui_006_menu_links` | メニューリンク | 各リンクの `href` が期待パスと一致し、「見積もり」から `/estimate/` に遷移 | PASS |
| UI-E2E-007 | `test_ui_007_unauthenticated_menu` | 未認証メニュー | 「ユーザーを登録」「ログイン」がDOMに存在し、「ログアウト」は存在しない | PASS |
| UI-E2E-008 | `test_ui_008_table_headers` | ジョブ一覧ヘッダー | 7列の見出しと順序が一致 | PASS |
| UI-E2E-009 | `test_ui_009_job_rows` | ジョブ行の構造 | 存在する各行が7セルで、価格セルに `¥` を含む | PASS |
| UI-E2E-010 | `test_ui_010_estimate_status` | 見積状態表示 | 各行の末尾が「未」または「済」、`bold` と対応する色クラスを持つ | PASS |
| UI-E2E-011 | `test_ui_011_monthly_total` | 未見積合計行 | 行が1件存在し、ラベルと `¥1,234円` 形式の金額が表示される | PASS |
| UI-E2E-012 | `test_ui_012_no_horizontal_overflow` | 横方向のはみ出し | `scrollWidth <= clientWidth` | PASS |
| UI-E2E-013 | `test_ui_013_nav_main_no_overlap` | 領域の重なり | `nav` と `main` の矩形が交差しない | PASS |
| UI-E2E-014 | `test_ui_014_no_javascript_errors` | JavaScript未処理例外 | ページ読み込み時の `pageerror` が0件 | PASS |
| UI-E2E-015 | `test_ui_015_static_assets` | 静的リソース | `/static/` のHTTP 4xx/5xxとリクエスト失敗がなく、CSS・JSタグが存在 | PASS |

## 4. 画面別の期待仕様

### 4.1 共通ナビゲーション

認証済みの場合、`nav #menu` に次の順で7項目を表示する。

1. トップ — `/top/`
2. プロジェクトを登録 — `/project/`
3. ジョブを登録 — `/record/`
4. ジョブを更新 — `/update/`
5. 見積もり — `/estimate/`
6. 管理画面 — `/admin/`
7. ログアウト — `/logout/`

未認証の場合は「ユーザーを登録」「ログイン」のリンクが存在し、ログアウトリンクは表示しない。現行テストは未認証リンクの **DOMへの存在** を確認しており、可視状態や実際のクリック遷移までは確認していない。

### 4.2 トップページのテーブル

列見出しは以下の7項目。

`ジョブタイトル` / `プロジェクト名` / `受注日` / `クライアント` / `代理店` / `価格` / `見積書`

ジョブ行 `tr.jobs` の末尾セルは、未見積の場合「未」+ `red bold`、見積済の場合「済」+ `green bold` とする。合計行 `tr.monthly_total_price` は「未見積合計金額」と円表記の金額を表示する。

## 5. 実行方法

プロジェクトルートで、既存のE2Eテスト環境とテスト用サーバー設定を用意したうえで実行する。

```bash
python -m pytest tests/e2e/test_ui_e2e.py -v
```

個別実行の例：

```bash
python -m pytest tests/e2e/test_ui_e2e.py::test_ui_015_static_assets -v
```

ブラウザを表示して確認する場合（Playwrightのpytest設定が対応している場合）：

```bash
python -m pytest tests/e2e/test_ui_e2e.py -v --headed
```

## 6. 判定上の注意点・制約

- **UI-E2E-009/010**：ジョブが0件の場合、各行に対するループが実行されないためPASSする。データが存在する場合の検証を保証するには、専用fixtureでジョブを用意する。
- **UI-E2E-012**：ページ全体の横はみ出しのみ検出する。内部スクロール領域や細かな配置崩れは対象外。
- **UI-E2E-013**：`nav` と `main` の矩形のみ比較する。意図的に重ねるデザインの場合は期待条件を調整する。
- **UI-E2E-014**：`pageerror` で検出できる未処理例外が対象。`console.error()` の出力やすべての通信障害を網羅するものではない。
- **UI-E2E-015**：HTTPエラーとリクエスト失敗を確認するが、CSSの見た目や全画像の視覚品質は比較しない。
- 本テストではスクリーンショット差分比較、キーボード操作、アクセシビリティ監査、モバイル・レスポンシブ表示を実施しない。

## 7. 保守・改善候補

- ジョブ一覧のテストデータをfixtureで準備し、空一覧・未見積・見積済の各状態を必ず検証する。
- 共通ナビゲーションをトップ以外の画面でも確認し、相対パスによる静的ファイル読み込みの不具合を検出する。
- JavaScriptの操作イベントがある場合、初期表示だけでなくクリック後のエラーも検証する。
- 必要に応じて固定Viewportでのスクリーンショット差分比較を追加する。

## 8. 実行結果まとめ

**15件実行・15件PASS**（ユーザー報告）。PC向けトップページの基本描画、共通ナビゲーション、ジョブ一覧の表示構造、主要レイアウト、JavaScript例外、静的リソース読み込みについて、現行テスト条件下で期待結果を満たした。
