# GIF Animation Web App

Streamlit で動く GIF アニメ生成アプリです。  
ベース画像を生成し、その画像をもとに複数コマの画像を作ってから GIF にまとめます。

このアプリは Python 3.13 環境で作成しています。

## ファイル構成

- `main.py`
  Streamlit の画面本体です。ベース画像生成、コマ画像生成、GIF 作成の UI と状態管理を行います。
- `openai_client.py`
  Azure OpenAI API の呼び出しをまとめています。ベース画像生成、動きの分解、各コマ画像の生成を担当します。
- `gif_maker.py`
  複数の PNG バイト列から GIF を生成します。
- `requirements.txt`
  現在のコードで使用している Python ライブラリ一覧です。
- `startup.sh`
  起動補助用ファイルです。ローカルの Windows PowerShell では通常 `streamlit run main.py` で起動できます。

## 必要な API

このアプリでは Azure OpenAI を使います。

- 画像生成 API
  ベース画像の生成に使用します。
- Chat Completions API
  ユーザーが指定した動きを複数コマの説明文に分解するために使用します。
- 画像編集 API
  ベース画像をもとに、各コマの画像へ変化させるために使用します。

現在のコードでは `openai_client.py` から次のモデル名を使っています。

- `gpt-image-1-mini`
  ベース画像生成と image-to-image のコマ画像編集に使用。
- `gpt-4.1-mini`
  動きの説明を JSON 化するために使用。

## Azure OpenAI の価格について

Azure OpenAI の価格は、使うモデル、デプロイ方式、入力と出力の使用量によって変わります。固定額ではなく、主に次の課金考え方があります。

- `Standard`
  従量課金です。入力や出力の利用量に応じて課金されます。
- `Provisioned`
  PTU ベースの確保型です。一定のスループットを予約して使う運用向けです。
- `Batch API`
  一部モデルではバッチ実行向けの価格体系があります。

さらに、`Global`、`Data Zone`、`Regional` などのデプロイ方式があり、価格や配置できる場所、データ処理の境界条件が異なります。価格は更新される可能性があるため、実際の見積もり前に公式価格ページの最新情報を確認してください。

公式価格ページ:

- https://azure.microsoft.com/ja-jp/pricing/details/azure-openai/

## Azure OpenAI の準備

Azure 側で次を準備してください。

1. Azure OpenAI リソースを作成する
2. `gpt-image-1-mini` が使えるデプロイ先を用意する
3. `gpt-4.1-mini` が使えるデプロイ先を用意する
4. API キーとエンドポイントを控える

このコードは Azure OpenAI SDK の `AzureOpenAI(...)` を使っており、`model=` に直接モデル名を渡しています。  
環境によっては、Azure Portal 側で実際のデプロイ名をモデル名と同じにしておくのが分かりやすいです。

### Azure OpenAI リソースの作成方法

Azure portal での基本的な流れは次の通りです。

1. Azure portal にサインインする
2. `リソースの作成` から `Azure OpenAI` を検索する
3. `作成` を選ぶ
4. `サブスクリプション`、`リソース グループ`、`リージョン`、`名前`、`価格レベル` を設定する
5. リソース作成後に対象リソースを開く
6. モデルのデプロイ画面で必要なモデルをデプロイする
7. `キー` と `エンドポイント` を取得する

公式手順:

- https://learn.microsoft.com/ja-jp/azure/foundry-classic/openai/how-to/create-resource?pivots=web-portal

### モデルをデプロイできるリージョンの制限

Azure OpenAI は、どのモデルでもすべてのリージョンにデプロイできるわけではありません。モデルの提供状況はリージョンとクラウドによって変わります。

このアプリで使っている `gpt-image-1-mini` と `gpt-4.1-mini` も、事前に対応リージョンを確認してから Azure OpenAI リソースを作成する必要があります。先にリソースだけ作っても、そのリージョンでは目的のモデルをデプロイできないことがあります。

対応リージョン確認先:

- https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure

## 環境変数

PowerShell では起動前に次の環境変数を設定してください。

```powershell
$env:AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
$env:AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
```

### 各環境変数の意味

- `$env:AZURE_OPENAI_API_KEY`
  Azure OpenAI の API キーです。
- `$env:AZURE_OPENAI_ENDPOINT`
  Azure OpenAI のエンドポイント URL です。通常は `https://<resource-name>.openai.azure.com/` の形式です。

## セットアップ

1. 仮想環境を作成する
2. 依存をインストールする
3. 環境変数を設定する
4. Streamlit を起動する

例:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
$env:AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"

streamlit run main.py
```

## `startup.sh` の使い方

`startup.sh` は次の内容です。

```bash
#!/usr/bin/env bash
set -e

PORT_VALUE=${PORT:-8000}

exec streamlit run main.py \
  --server.address 0.0.0.0 \
  --server.port $PORT_VALUE \
  --server.headless true
```

役割は次の通りです。

- App Service などの Linux 環境で `PORT` が渡されたとき、そのポートで Streamlit を起動する
- `0.0.0.0` で待ち受けて外部からアクセスできるようにする
- `headless true` でサーバー環境向けの設定にする

### Azure Web App にデプロイする場合

Azure では次の選択で Web アプリを作成する場合に使います。

1. `App Service` を開く
2. `Web アプリ` を作成する
3. `ランタイム スタック: Python 13` を選ぶ
4. `オペレーティング システム: Linux` を選ぶ
5. `価格プラン: Free F1` を選ぶ

その後の基本的な流れ:

1. 上記設定で Web アプリを作成する
2. デプロイ対象のファイルを ZIP にまとめる
3. Azure portal から ZIP デプロイを実行する
4. `設定` → `環境変数` で Azure OpenAI の環境変数を追加する
5. `設定` → `App Service 設定` 　→　`構成`　→　`スタック設定`　下部にあるStartup Command に `bash startup.sh` を入力する
6. 保存してApp Serviceを再起動する

ZIP に含める主なファイル:

- `main.py`
- `openai_client.py`
- `gif_maker.py`
- `requirements.txt`
- `startup.sh`

Azure 側で設定しておく環境変数の例:

```text
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
```

Azure Web App on Linux では `PORT` はプラットフォーム側から渡される想定なので、`startup.sh` 側で明示設定する必要はありません。`startup.sh` はその値を受け取って Streamlit に渡します。

Azure portal で Startup Command を入力する場合は、次のように設定します。

```text
bash startup.sh
```

デプロイ後に起動しない場合は次を確認してください。

- `startup.sh` がリポジトリに含まれていること
- アプリのルートで `main.py` が参照できること
- ZIP 展開後のアプリ ルートに `requirements.txt` と `startup.sh` があること
- Azure Web App のアプリ設定に `AZURE_OPENAI_API_KEY` と `AZURE_OPENAI_ENDPOINT` が入っていること
- インストール対象に `streamlit`、`openai`、`Pillow` が含まれていること
- Azure portal の Startup Command に `bash startup.sh` が設定されていること
- `Free F1` は無料枠のため、GitHubからの継続的なデプロイは不可で起動時間や利用上限の面で制約があること

## 使い方

1. ベース画像用の説明を入力する
2. `ベース画像を生成` を押す
3. 動きの説明を入力する
4. コマ数を選ぶ
5. `コマ画像を生成して確認する` を押す
6. 生成されたコマ画像を確認する
7. GIF の 1 コマあたりの秒数を調整する
8. `確認したコマ画像からGIFアニメを作成` を押す
9. GIF を確認し、保存する場合はダウンロードする

## 補足

- コマ数は `2` から `8` まで選べます。
- GIF のコマ表示時間は Streamlit 上で調整できます。
- 生成結果は API 応答に依存するため、コマ説明 JSON が崩れた場合は画面上にエラーを出します。
- Azure OpenAI の価格、利用可能モデル、対応リージョンは変わることがあるため、構築前に公式ドキュメントの最新情報を確認してください。
