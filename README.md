# Debate Agent

## 概要

ユーザが入力した議題について、2つのLLMエージェントが異なる立場から討論し、最後にJudge役のLLMが議論内容を評価するLangGraphベースのアプリケーションです。

討論前にPersona GeneratorがDebater A / Bそれぞれの人物像と討論アプローチを生成し、「分析型 / 実践型」の異なる視点から議論を行います。

StreamlitによるWeb UIを用意しており、利用者自身のOpenAI API Keyを入力して実行できます。

---

## 目的・アピールポイント

本プロジェクトは、LLMアプリケーション開発のポートフォリオとして作成しています。

単純にLLMへ1回質問する構成ではなく、Topic Validator、Persona Generator、Debater A / B、Judgeという複数の役割をLangGraph上で連携させ、状態管理・条件分岐・ループ・評価までを一連の処理として実装しています。

主な実装・設計ポイントは以下です。

- LangGraphによるState / Node / Conditional Edge / ループ制御
- LCELによるPrompt / LLM / Output Parserのチェーン構成
- Pydantic + Structured Outputによる出力形式の固定
- Personaを用いたRole-Based Agent
- Debater A / Bとは別のJudgeによる討論評価
- APIコストを意識したコンテキスト設計
- StreamlitによるWeb UI
- UIとエージェント本体の分離
- 利用者自身のOpenAI API Keyを使う構成
- `requirements.txt` による別環境での再現確認

---

## 主な機能

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

## 処理フロー

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

Topic Validatorで議題を判定し、討論可能な場合のみPersona生成と討論へ進みます。

Debater A → Debater Bを1ターンとして繰り返し、既定では2ターン、つまりDebater A / Bがそれぞれ2回ずつ発言します。

討論終了後、Judgeが全履歴を参照して評価を行います。

---

## 出力例

以下は、「一緒に昼寝をするなら、犬と猫のどちらがよいか？」を議題とした実際のアプリ実行例です。

<details>
<summary>サンプル出力を見る</summary>

### 入力議題

一緒に昼寝をするなら、犬と猫のどちらがよいか？

### 討論

**Debater A**

犬と一緒に昼寝をする方がよいと考えます。まず快適さを決める条件を分けて考えましょう。犬は体温が安定しやすく、飼い主のそばで一定の姿勢を保つ個体なら、安心できる「一緒に休む時間」になりやすいです。起きた後も散歩や遊びへ自然に移れるため、生活リズムとの相性も良いでしょう。もちろん、寝返りが多い大型犬や、暑がりで布団から出入りする犬なら別途工夫が必要です。猫は静かで省スペースな点が魅力ですが、気分で移動したり、夜行性の影響で昼寝を中断したりします。犬なら、性格・体格・寝床の広さを整えることで、安心感と同じ時間を過ごす実感を両立しやすいのです。

**Debater B**

犬の安定した姿勢や、起きてから散歩へ移りやすい点は確かに魅力ですね。ただ、実際に昼寝してみると、猫のほうが「静かに休む」という目的には合わせやすいと感じます。ベッドの端や毛布の上で丸くなれば、寝返りの邪魔になりにくく、足音や寝返りで起こされることも比較的少ないです。猫が途中で移動しても、短時間の昼寝ならむしろ互いに無理がありません。専用の小さな毛布を腰元に置けば、猫はそこで眠り、自分は広く使えます。犬の温かさや親密さも良いですが、省スペースで距離を調整しやすい猫のほうが、日常には取り入れやすいと思います。

**Debater A**

猫の省スペース性と、距離を調整しやすい点は確かに昼寝向きですね。ただ、まず快適さを決める条件を分けて考えましょう。①寝姿勢の安定、②安心感、③起床後の生活リズムです。猫は移動が自由なぶん、昼寝中に場所を変えたり、急に起きて活動したりする場合があります。一方、落ち着いた犬なら、飼い主の足元や隣で一定の姿勢を保ち、体温と重みが「一緒に休んでいる」実感につながります。さらに起床後に散歩や軽い遊びへ移行しやすく、昼寝が生活リズムを整えるきっかけにもなります。もちろん大型犬で寝床が狭い場合は工夫が必要ですが、体格と寝床を合わせれば、犬のほうが安心感と休息後の活動性を両立しやすいと思います。

**Debater B**

犬の体温や、起床後に散歩へ移れる安心感は魅力ですね。ただ、実際に昼寝してみると、休息中の静けさと距離の調整では猫のほうが扱いやすいと思います。毛布の上で猫が丸くなり、足元や脇で眠ってくれれば、体重で寝返りを妨げられにくく、必要なら少し離れたクッションへ移動できます。犬は落ち着いていても、寝返りや呼吸の動きが大きく、散歩の時間を察して起こしてくることもあります。猫が途中で場所を変える点も、短時間の昼寝ならむしろ利点です。寝室の隅に猫用ベッドを置けば、同じ空間で互いに無理なく休めます。

### 今回のPersona

「分析型 / 実践型」は能力差ではなく、主張を組み立てるアプローチの違いを表します。

**Debater A**

- 討論アプローチ: 分析型
- 立場: 犬と一緒に昼寝をする方がよい
- 人物像: 相手の立場にも配慮しながら、昼寝の快適さを決める条件を丁寧に整理するタイプ。犬との昼寝についても、性格や体格、寝室環境など具体的な条件に結びつけて考える。

**Debater B**

- 討論アプローチ: 実践型
- 立場: 猫と一緒に昼寝をする方がよい
- 人物像: 実際の昼寝の場面を思い浮かべながら、動物との距離感や寝心地を具体的に語るタイプ。相手の主張には、日常の状況や飼い主が取り入れやすい工夫を挙げて応じる。

### Judge結果

**判定:** Debater B の主張がより説得的  
**主張:** 猫と一緒に昼寝をする方がよい

**判定理由**  
Bは「一緒に昼寝」の中心目的を休息中の静けさ、寝返りへの影響、距離調整のしやすさとして具体化し、猫の省スペース性を毛布や猫用ベッドという実行可能な場面で支えた。Aの安心感・体温という利点は認めつつ、犬の動きや体重、散歩を察して起こす可能性を対抗根拠として示している。Aは起床後の散歩への移行を重視したが、それが昼寝自体の快適さを上回る理由は十分に示せていない。

**Debater A の良かった点**  
犬の体格・性格・寝床による条件差を認め、安定した姿勢や体温による安心感を具体的に説明した。猫の省スペース性も正面から認めたうえで自説を維持している。

**Debater B の良かった点**  
休息中に起こりうる寝返り、体重、移動、必要な距離といった利用場面に即して猫の利点を示した。犬の長所を踏まえながら、昼寝の目的により直接関係する反論を行っている。

</details>

---

## 討論アプローチ

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

## 使用技術

- Python
- OpenAI API
- LangChain
- LangGraph
- LCEL
- Structured Output
- Pydantic
- Streamlit

---

## 使用モデル

役割ごとにモデルを分けています。

- Topic Validator / Persona Generator / Debater
  - `gpt-5.6-luna`
- Judge
  - `gpt-5.6-terra`

Judgeは討論終了後に1回だけ実行します。

---

## 動作環境

開発・動作確認では以下の環境を使用しています。

- OS: Windows 11
- Python: 3.11
- Streamlit: 1.64.0
- LangChain: 1.4.2
- langchain-openai: 1.6.2
- LangGraph: 1.2.11
- Pydantic: 2.x

また、開発時に使用した環境とは別に新規のPython 3.11環境を作成し、`requirements.txt` のみから依存関係を構築して、Streamlit UIから討論実行まで正常に動作することを確認しています。

---

## プロジェクト構成

```text
langgraph-debate-agent/
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

### 1. リポジトリを取得

Gitを利用する場合：

```bash
git clone https://github.com/masatoppp/langgraph-debate-agent.git
cd langgraph-debate-agent
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

## APIキー

Streamlit画面のサイドバーから、利用者自身のOpenAI API Keyを入力します。

API Keyはソースコードへ直接記述せず、`app.py` から次のように実行時にバックエンドへ渡します。

```python
result = run_debate(topic, api_key)
```

バックエンドでは、渡されたAPI Keyを `ChatOpenAI` の生成時に利用します。

GitHubへAPI Keyを含めない構成としています。

---

## 入力例

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

## 対象外の議題

次のような入力は討論対象外とします。

- 客観的事実・数値・定義などによって答えがほぼ一意に決まる質問
- 単なる事実確認・手続き確認
- 政治・宗教・戦争・差別など、強い思想的対立を含むテーマ

Topic Validatorが最初に判定し、対象外の場合は討論を開始しません。

---

## APIコストを意識した設計

APIコストを抑えるため、次の設計を採用しています。

- Debater A → Debater Bを1ターンとして、既定では2ターン
- Debaterには議論履歴全体を毎回渡さない
- 各Debaterへ渡すのは相手の直前の発言のみ
- 全履歴はStateへ保持
- Judgeだけが最後に討論履歴全体を参照
- Judgeは討論終了後に1回だけ実行
- 繰り返し実行される役割とJudgeで使用モデルを分ける

---

## 設計ポイント

### LangGraph

エージェント全体の状態遷移、条件分岐、討論ループを管理します。

Topic Validatorによる条件分岐や、Debater A / Bの討論継続判定をGraph上で制御しています。

### LCEL

各Node内部で、Prompt / LLM / Output Parserを接続するために使用しています。

LangGraphがアプリケーション全体の処理フローを担当し、LCELが各Node内部のLLM処理を担当する構成です。

### Structured Output

Topic Validator、Persona Generator、Judgeの出力をPydantic Schemaへ固定しています。

自由文だけに依存せず、後続処理で必要となる値を一定の形式で扱えるようにしています。

### Role-Based Agent

Debater A / Bには同じDebater用モデルを使用し、Personaと立場を変えることで異なる役割として動作させています。

能力差を設定するのではなく、「分析型 / 実践型」という主張の組み立て方の違いをPersonaへ与えています。

### LLM Judge

討論終了後、Judgeが討論履歴全体を確認して、どちらの主張がより説得的であったかを評価します。

Judgeは対象そのものの優劣ではなく、今回の討論における主張・根拠・反論の内容を評価するようPromptを設計しています。

### UIとバックエンドの分離

UIとエージェント本体を分離しています。

```text
app.py
  ↓
run_debate(topic, api_key)
  ↓
debate_agent.py
```

これにより、StreamlitのUI処理とLangGraphを使ったエージェント処理を分けて管理できます。

Notebook・Web UI・エージェント本体をそれぞれ独立して確認しやすい構成としています。

### 再現性

開発時に使用した環境とは別に、新規のPython 3.11環境を作成し、

```bash
pip install -r requirements.txt
```

から依存関係を構築しました。

その後、

```bash
pip check
```

で依存関係に問題がないことを確認し、Streamlit UIの起動から討論処理まで正常に実行できることを確認しています。

---

## 依存ライブラリ

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

## 今後の改善点

- Judgeの評価基準をさらに調整し、討論アプローチによる評価偏りを減らす
- 「分析型 / 実践型」以外の討論アプローチを追加する
- 討論ターン数をStreamlit UIから変更できるようにする
- 利用するモデルをUIから選択できるようにする
- LangSmithなどを使った実行ログや評価結果の可視化
- 複数回の討論結果を保存し、PersonaやJudge結果の傾向を比較できるようにする
- Web検索やRAGを組み合わせ、外部情報を根拠として利用できる討論へ拡張する

---

## 既知の制約

- LLMの出力には実行ごとの揺らぎがあります。
- Judgeの評価も確定的な正解ではありません。
- 「分析型 / 実践型」に能力差が生じないようPromptで制御していますが、LLM由来のスタイル偏りを完全に排除できるとは限りません。
- 現在は外部情報検索やRAGを組み込んでいないため、討論はモデルが持つ知識と入力された議題をもとに行われます。
- API利用料金は使用モデル、入力トークン数、出力トークン数などによって変動します。

---

## 補足

- 本アプリの実行には利用者自身のOpenAI API Keyが必要です。
- API KeyはGitHubへ含めず、Streamlit UIから実行時に入力する構成です。
- Notebookは実装過程・技術要素・設計意図を確認するための技術解説用として残しています。
- Streamlit版は実際の操作・動作確認用、Notebook版は実装内容の理解・確認用という位置付けです。
