# Debate Agent

ユーザが入力した議題について、2つのLLMエージェントが異なる立場から討論し、最後にJudge役のLLMが議論内容を評価するLangGraphベースのアプリケーションです。

StreamlitによるWeb UIを用意しており、利用者自身のOpenAI API Keyを入力して実行できます。

---

## Features

- Topic Validatorによる議題判定
  - `VALID_DEBATE`
  - `NOT_DEBATABLE`
  - `RESTRICTED_TOPIC`
- Persona GeneratorによるDebater A / Bの人物像生成
- 「分析型 / 実践型」の討論アプローチを実行ごとにランダム割り当て
- LangGraphによる複数ターンの討論制御
- Judgeによる討論全体の評価
- Structured Output + Pydanticによる出力形式の固定
- StreamlitによるWeb UI
- 利用者自身のOpenAI API Keyを使う構成
- APIコストを意識した履歴管理
- UIとエージェント本体を分離した構成
- `requirements.txt` から新規環境を再構築できる構成

---

## Demo Flow

```text
User
  ↓
Topic Validator
  ├─ NOT_DEBATABLE ─────→ END
  ├─ RESTRICTED_TOPIC ──→ END
  └─ VALID_DEBATE
          ↓
    Persona Generator
          ↓
      Debater A
          ↓
      Debater B
          ↓
      Turn Check
       ├─ 継続 → Debater A
       └─ 終了 → Judge → END
```

---

## Debate Approaches

Debater A / Bには能力差を設定せず、主張を組み立てるアプローチだけを変えています。

### 分析型

- 条件整理
- 比較
- 因果関係
- 論点の構造化

### 実践型

- 具体例
- 実際の利用場面
- 実行可能性
- 体験に基づく説明

どちらのアプローチをDebater A / Bへ割り当てるかは、実行ごとにランダムで決定します。

---

## Tech Stack

- Python
- OpenAI API
- LangChain
- LangGraph
- LCEL
- Structured Output
- Pydantic
- Streamlit

---

## Models

役割ごとにモデルを分けています。

- Topic Validator / Persona Generator / Debater
  - `gpt-5.6-luna`
- Judge
  - `gpt-5.6-terra`

討論は既定で2往復です。

---

## Project Structure

```text
debate_agent/
├─ app.py
├─ debate_agent.py
├─ debate_agent.ipynb
├─ requirements.txt
├─ README.md
└─ .gitignore
```

### `app.py`

Streamlit UIを担当します。

- OpenAI API Key入力
- 議題入力
- 討論開始
- 討論履歴表示
- Persona表示
- Judge結果表示

### `debate_agent.py`

エージェント本体です。

- LLM設定
- Prompt
- LCEL
- Topic Validator
- Persona Generator
- Debater A / B
- Judge
- State
- LangGraph

Streamlitからは次のインターフェースで呼び出します。

```python
result = run_debate(topic, api_key)
```

### `debate_agent.ipynb`

技術解説用Notebookです。

LangGraph / LCEL / Structured Output / Persona / Judgeなどを段階的に確認できます。

---

## 別環境での実行方法

本アプリは、GitHubからプロジェクト一式を取得し、利用者自身のPython環境とOpenAI API Keyで実行できます。

新規のPython 3.11環境を作成し、`requirements.txt` のみから依存関係を構築して動作確認を行っています。

### 1. Repositoryを取得

Gitを利用する場合：

```bash
git clone <repository-url>
cd debate_agent
```

または、GitHubの **Download ZIP** から取得して展開してください。

### 2. Python環境を作成

Python 3.11を想定しています。

#### Anacondaの場合

```bash
conda create -n debate_agent python=3.11 -y
conda activate debate_agent
```

#### venvの場合

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 3. 必要ライブラリをインストール

```bash
pip install -r requirements.txt
```

依存関係を確認する場合：

```bash
pip check
```

正常な場合は以下のように表示されます。

```text
No broken requirements found.
```

### 4. Streamlitを起動

```bash
python -m streamlit run app.py
```

起動後、ブラウザでDebate AgentのWeb UIが表示されます。

### 5. OpenAI API Keyを入力

画面左側のサイドバーに、自分のOpenAI API Keyを入力してください。

```text
OpenAI API Key
[ *************** ]
```

API Keyを入力すると、サイドバーに受付メッセージが表示されます。

API Keyはソースコードへ直接記述せず、実行時にのみ利用します。

### 6. 議題を入力して実行

例：

```text
犬派 vs 猫派
```

「討論開始」を押すと、以下の順に処理されます。

1. Topic Validator
2. Persona Generator
3. Debater A / B
4. Judge

最終的に、討論履歴・Persona・Judgeの判定結果が画面に表示されます。

> OpenAI APIの利用には、ChatGPTの契約とは別にAPI利用料金が発生します。

---

## API Key

Streamlit画面のサイドバーから、自分のOpenAI API Keyを入力してください。

API Keyはソースコードへ直接記述しません。

`app.py` から `run_debate(topic, api_key)` へ実行時に渡し、`ChatOpenAI` の生成時に利用します。

GitHubへAPI Keyを含めない構成としています。

---

## Input Examples

```text
犬派 vs 猫派
```

```text
旅行では、事前に細かく計画する方が楽しみやすいか、
それとも現地で柔軟に決める方が楽しみやすいか
```

```text
新しい技術を学ぶとき、
書籍から始めるのと実際にコードを書くのではどちらが良いか
```

```text
一緒にいてより落ち着くのは犬か猫か。
犬はやや活発で、猫は気まぐれであるという
それぞれの不利な点を踏まえて比較する。
```

---

## Topics Not Handled

次のような入力は討論対象外とします。

- 客観的事実・数値・定義などによって答えがほぼ一意に決まる質問
- 単なる事実確認・手続き確認
- 政治・宗教・戦争・差別など、強い思想的対立を含むテーマ

Topic Validatorが最初に判定し、対象外の場合は討論を開始しません。

---

## Cost-conscious Design

APIコストを抑えるため、次の設計を採用しています。

- 討論は既定で2往復
- Debaterには議論履歴全体を毎回渡さない
- 各Debaterへ渡すのは相手の直前の発言のみ
- 全履歴はStateへ保持
- Judgeだけが最後に討論履歴全体を参照
- Judgeは討論終了後に1回だけ実行

---

## Design Points

### LangGraph

エージェント全体の状態遷移、条件分岐、討論ループを管理します。

### LCEL

各Node内部のPrompt / LLM / Output Parserを接続します。

### Structured Output

Topic Validator、Persona Generator、Judgeの出力をPydantic Schemaへ固定しています。

### Role-based Agent

同一モデルを使いながら、Personaと立場を変えることでDebater A / Bを別の役割として動作させています。

### UI / Backend Separation

UIとエージェント本体を分離しています。

```text
app.py
  ↓
run_debate(topic, api_key)
  ↓
debate_agent.py
```

これにより、Notebook・Web UI・エージェント本体をそれぞれ独立して確認しやすい構成にしています。

### Reproducibility

開発時に使用した環境とは別に、新規のPython 3.11環境を作成し、

```bash
pip install -r requirements.txt
```

から依存関係を構築しています。

その後、

```bash
pip check
```

で依存関係に問題がないことを確認し、Streamlit UIから討論処理まで正常に実行できることを確認しています。

---

## Requirements

主な依存ライブラリは以下です。

```text
streamlit==1.64.0
langchain==1.4.2
langchain-openai==1.6.2
langgraph==1.2.11
pydantic>=2.0,<3.0
sqlalchemy>=1.4,<3.0
python-dotenv>=0.21.0
```

実際のインストールには `requirements.txt` を使用してください。

---

## Known Limitations

- LLMの出力には実行ごとの揺らぎがあります。
- Judgeの評価も確定的な正解ではありません。
- 分析型 / 実践型の能力差を作らないようPromptで制御していますが、LLM由来のスタイル偏りを完全に排除できるとは限りません。
- 外部情報検索やRAGは本アプリには組み込んでいません。
- API利用料金は使用モデル、入力、出力によって変動します。

---

## Purpose

本プロジェクトは、LLMアプリケーション開発のポートフォリオとして作成しています。

特に以下の実装を目的としています。

- LangGraphを使ったState / Node / Conditional Edge
- LCELによる処理チェーン
- Structured Output
- Personaを用いたRole-Based Agent
- LLM Judge
- APIコストを意識したコンテキスト設計
- StreamlitによるWeb UI
- UIとバックエンドの分離
- 別環境で再現可能なプロジェクト構成
