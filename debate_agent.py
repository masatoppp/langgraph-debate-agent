import random
from typing import Literal

from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, START, END


# ============================================
# 実行設定
# ============================================

COST_MODEL = "gpt-5.6-luna"
JUDGE_MODEL = "gpt-5.6-terra"
MAX_TURNS = 2


# ============================================
# Schema
# ============================================

class TopicValidationResult(BaseModel):
    category: Literal[
        "VALID_DEBATE",
        "NOT_DEBATABLE",
        "RESTRICTED_TOPIC"
    ] = Field(
        description="入力されたテーマの分類結果"
    )

    reason: str = Field(
        description="その分類にした理由"
    )

    normalized_topic: str | None = Field(
        default=None,
        description="議論可能な場合に、議題として自然な形へ整えた文章"
    )


class DebaterPersona(BaseModel):
    position: str = Field(
        description="担当する立場"
    )

    style_type: Literal["分析型", "実践型"] = Field(
        description="Debaterに割り当てる討論アプローチの大分類"
    )

    personality: str = Field(
        description="能力差ではなく人物としての違いを表す人物像"
    )

    values: list[str] = Field(
        description="議論で重視する価値観"
    )

    thinking_style: str = Field(
        description="物事をどのように考えるかという思考スタイル"
    )

    speaking_style: str = Field(
        description="議論時の話し方の特徴"
    )


class PersonaGenerationResult(BaseModel):
    debater_a: DebaterPersona
    debater_b: DebaterPersona


class JudgeResult(BaseModel):
    winner: Literal["A", "B", "DRAW"] = Field(
        description="討論の判定結果。Aの主張がより説得的ならA、BならB、実質的な差がなければDRAW"
    )

    reason: str = Field(
        description="判定理由。評価基準に基づき簡潔に説明する"
    )

    strengths_a: str = Field(
        description="Debater A の良かった点"
    )

    strengths_b: str = Field(
        description="Debater B の良かった点"
    )


class DebateState(BaseModel):
    topic: str = Field(
        description="ユーザが入力した元の議題"
    )

    normalized_topic: str = Field(
        default="",
        description="Topic Validator が整形した議題"
    )

    persona_a: DebaterPersona | None = Field(
        default=None,
        description="Debater A のPersona"
    )

    persona_b: DebaterPersona | None = Field(
        default=None,
        description="Debater B のPersona"
    )

    debate_history: list[str] = Field(
        default_factory=list,
        description="Debater A / B の発言履歴"
    )

    turn_count: int = Field(
        default=0,
        description="現在の議論ターン数"
    )

    validation_category: str = Field(
        default="",
        description="Topic Validator の分類結果"
    )

    validation_reason: str = Field(
        default="",
        description="Topic Validator の判定理由"
    )

    judgment: dict = Field(
        default_factory=dict,
        description="Judge の最終判定結果"
    )


# ============================================
# Prompt
# ============================================

validator_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
あなたは討論エージェントの入力テーマを判定するValidatorです。

入力されたテーマを、以下の3種類のいずれかに分類してください。

1. VALID_DEBATE
   - 複数の立場が合理的に成立する
   - 価値観、好み、目的、評価基準によって結論が変わり得る
   - 政治・宗教・戦争・差別など、強い思想的対立を含まない

2. NOT_DEBATABLE
   - 客観的事実、数値、定義などによって答えがほぼ一意に決まる
   - 単なる事実確認や手続き確認である

3. RESTRICTED_TOPIC
   - 政治、宗教、戦争、差別など、今回の討論エージェントでは扱わないテーマ

VALID_DEBATE の場合は、元の意味を変えない範囲で
議論しやすい自然な文章に整えて normalized_topic に格納してください。
対立する2つの立場・選択肢の登場順は変更しないでください。

NOT_DEBATABLE または RESTRICTED_TOPIC の場合は
normalized_topic を null にしてください。

reason は判定根拠が分かる1〜2文程度の簡潔な説明にしてください。
"""
        ),
        (
            "human",
            "入力テーマ: {topic}"
        )
    ]
)


persona_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
あなたは討論エージェント用のPersona Generatorです。

与えられた議題について、
Debater A と Debater B のPersonaを生成してください。

【ルール】

- 議題に登場する順番を維持してください。
- 最初の立場を Debater A、次の立場を Debater B としてください。
- Debater A の style_type は「{style_a}」、Debater B の style_type は「{style_b}」にしてください。

【討論アプローチ】

- 分析型は、条件整理・比較・因果関係・論点の構造化を重視してください。
- 実践型は、具体例・実際の利用場面・実行可能性・体験に基づく説明を重視してください。
- 分析型と実践型はアプローチが異なるだけで、知識量・論理性・知能・議論能力には優劣をつけないでください。
- 実践型を感覚的・非論理的な人物として生成しないでください。明確な理由を示し、相手の論点へ具体的に応答できる人物にしてください。
- 分析型を自動的に高度・優秀な人物として生成しないでください。整理した論点を必ず議題や具体的な根拠へ結びつける人物にしてください。

【Persona】

- 違いを持たせるのは人物像、価値観、思考スタイル、話し方です。
- 一方だけが極端、非合理的、攻撃的にならないようにしてください。
- どちらの立場も合理的に主張できる人物にしてください。
- 年齢、性別など議論に不要な属性は設定しないでください。
- 2人のPersonaは明確に異なるものにしてください。
- Personaの違いが議論内容や話し方に反映されるようにしてください。
- 親しみやすく自然な話し方の特徴を設定してください。
- 攻撃的、断定的すぎる話し方にはしないでください。
- personality / thinking_style / speaking_style はそれぞれ1〜2文程度にしてください。
- values は各Debaterにつき3項目程度にしてください。
"""
        ),
        (
            "human",
            "議題: {topic}"
        )
    ]
)


debater_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
あなたは討論に参加するDebaterです。

以下のPersonaと立場を維持しながら議論してください。

【基本ルール】

- 自分の立場を一貫して支持してください。
- Personaの人物像、価値観、思考スタイル、話し方を反映してください。
- 初回発言では、自分の立場の主張から始めてください。
- 相手の発言がある場合は、その内容を一度受け止めたうえで自分の立場から反論してください。
- 相手を攻撃したり、人格を否定したりしないでください。
- 親しみやすく自然な口調で話してください。
- 単なる感想だけではなく、明確な理由や具体例を含めてください。
- 1回の発言は250〜400文字程度を目安にしてください。
- 同じ主張の繰り返しを避け、相手の直前の発言に対して新しい論点を1つ以上加えてください。

【討論アプローチ】

あなたの討論アプローチは「{style_type}」です。

- 分析型の場合は、条件整理・比較・因果関係・論点の構造化を中心に説得してください。
- 実践型の場合は、具体例・実際の利用場面・実行可能性・体験に基づく説明を中心に説得してください。
- どちらのアプローチでも、主張と理由のつながりを明確にし、相手の論点へ具体的に応答してください。
- 分析型だから論理性が高い、実践型だから感覚的という扱いにはしないでください。

【あなたの立場】
{position}

【あなたの人物像】
{personality}

【重視する価値観】
{values}

【思考スタイル】
{thinking_style}

【話し方】
{speaking_style}
"""
        ),
        (
            "human",
            """
【議題】
{topic}

【相手の直前の発言】
{opponent_message}

あなたの次の発言を生成してください。
"""
        )
    ]
)


judge_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
あなたは討論を公平に評価するJudgeです。

Debater A と Debater B の議論全体を読み、
「今回の討論でどちらがより説得力のある議論を行ったか」を評価してください。

【評価基準】

- 議題に直接答えているか
- 主張と理由のつながりが明確か
- 相手の主張を理解したうえで具体的に反論できているか
- 根拠・具体例・利用場面が主張を十分に支えているか
- 反論を受けても、自分の立場を一貫して発展させられているか

【スタイルの公平性】

- Debaterの討論アプローチや話し方の好みを判定材料にしないでください。
- 分析型の「整理されている」「比較項目が多い」「文章が構造化されている」といった形式そのものを加点しないでください。
- 実践型の具体例・実際の利用場面・実行可能性・体験に基づく説明も、主張を適切に支えている場合は分析的な整理と同等に評価してください。
- 実践型を感覚的・非論理的とみなしたり、分析型をより知的・高度とみなしたりしないでください。
- 重要なのは発言の形式ではなく、議題に対してどれだけ有効な根拠と反論を提示できたかです。

【判定ルール】

- Debaterの立場そのものを理由に有利・不利をつけないでください。
- 外部の情報を持ち込まず、実際に行われた議論内容のみを評価してください。
- テーマ自体が主観的でも、討論の質に差があれば A または B を選んでください。
- DRAW は、上記の評価基準を比較しても実質的な差が見つからない場合だけ選んでください。
- reason は2〜4文程度、strengths_a / strengths_b は各1〜2文程度で簡潔にしてください。
"""
        ),
        (
            "human",
            """
【議題】
{topic}

【討論内容】
{debate_history}

討論全体を評価してください。
"""
        )
    ]
)


# ============================================
# Persona style
# ============================================

PERSONA_STYLE_TYPES = ["分析型", "実践型"]


def assign_persona_styles():
    style_a, style_b = random.sample(PERSONA_STYLE_TYPES, k=2)
    return style_a, style_b


# ============================================
# Graph builder
# ============================================

def build_debate_agent(api_key: str):
    api_key = api_key.strip()

    if not api_key:
        raise ValueError("OpenAI API Keyが入力されていません。")

    persona_llm = ChatOpenAI(
        model=COST_MODEL,
        temperature=0.7,
        api_key=api_key
    )

    validator_llm = ChatOpenAI(
        model=COST_MODEL,
        temperature=0,
        api_key=api_key
    )

    debate_llm = ChatOpenAI(
        model=COST_MODEL,
        temperature=0.7,
        api_key=api_key
    )

    judge_llm = ChatOpenAI(
        model=JUDGE_MODEL,
        temperature=0,
        api_key=api_key
    )

    validator_chain = (
        validator_prompt
        | validator_llm.with_structured_output(TopicValidationResult)
    )

    persona_chain = (
        persona_prompt
        | persona_llm.with_structured_output(PersonaGenerationResult)
    )

    debater_chain = (
        debater_prompt
        | debate_llm
        | StrOutputParser()
    )

    judge_chain = (
        judge_prompt
        | judge_llm.with_structured_output(JudgeResult)
    )

    def topic_validator_node(state: DebateState):
        result = validator_chain.invoke(
            {"topic": state.topic}
        )

        return {
            "normalized_topic": result.normalized_topic or "",
            "validation_category": result.category,
            "validation_reason": result.reason
        }

    def persona_generator_node(state: DebateState):
        style_a, style_b = assign_persona_styles()

        result = persona_chain.invoke(
            {
                "topic": state.normalized_topic,
                "style_a": style_a,
                "style_b": style_b
            }
        )

        return {
            "persona_a": result.debater_a,
            "persona_b": result.debater_b
        }

    def debater_a_node(state: DebateState):
        persona = state.persona_a

        opponent_message = (
            state.debate_history[-1]
            if state.debate_history
            else "まだ相手の発言はありません。"
        )

        response = debater_chain.invoke(
            {
                "topic": state.normalized_topic,
                "position": persona.position,
                "style_type": persona.style_type,
                "personality": persona.personality,
                "values": "、".join(persona.values),
                "thinking_style": persona.thinking_style,
                "speaking_style": persona.speaking_style,
                "opponent_message": opponent_message
            }
        )

        return {
            "debate_history": state.debate_history + [
                f"Debater A:\n{response}"
            ]
        }

    def debater_b_node(state: DebateState):
        persona = state.persona_b
        opponent_message = state.debate_history[-1]

        response = debater_chain.invoke(
            {
                "topic": state.normalized_topic,
                "position": persona.position,
                "style_type": persona.style_type,
                "personality": persona.personality,
                "values": "、".join(persona.values),
                "thinking_style": persona.thinking_style,
                "speaking_style": persona.speaking_style,
                "opponent_message": opponent_message
            }
        )

        return {
            "debate_history": state.debate_history + [
                f"Debater B:\n{response}"
            ],
            "turn_count": state.turn_count + 1
        }

    def judge_node(state: DebateState):
        history_text = "\n\n".join(state.debate_history)

        result = judge_chain.invoke(
            {
                "topic": state.normalized_topic,
                "debate_history": history_text
            }
        )

        return {
            "judgment": result.model_dump()
        }

    def route_after_validation(state: DebateState):
        if state.validation_category == "VALID_DEBATE":
            return "persona_generator"

        if state.validation_category == "NOT_DEBATABLE":
            return "not_debatable"

        return "restricted_topic"

    def route_after_debate(state: DebateState):
        if state.turn_count < MAX_TURNS:
            return "debater_a"

        return "judge"

    def not_debatable_node(state: DebateState):
        return {}

    def restricted_topic_node(state: DebateState):
        return {}

    graph = StateGraph(DebateState)

    graph.add_node("topic_validator", topic_validator_node)
    graph.add_node("persona_generator", persona_generator_node)
    graph.add_node("debater_a", debater_a_node)
    graph.add_node("debater_b", debater_b_node)
    graph.add_node("judge", judge_node)
    graph.add_node("not_debatable", not_debatable_node)
    graph.add_node("restricted_topic", restricted_topic_node)

    graph.add_edge(START, "topic_validator")

    graph.add_conditional_edges(
        "topic_validator",
        route_after_validation,
        {
            "persona_generator": "persona_generator",
            "not_debatable": "not_debatable",
            "restricted_topic": "restricted_topic"
        }
    )

    graph.add_edge("persona_generator", "debater_a")
    graph.add_edge("debater_a", "debater_b")

    graph.add_conditional_edges(
        "debater_b",
        route_after_debate,
        {
            "debater_a": "debater_a",
            "judge": "judge"
        }
    )

    graph.add_edge("judge", END)
    graph.add_edge("not_debatable", END)
    graph.add_edge("restricted_topic", END)

    return graph.compile()


# ============================================
# Public interface for Streamlit
# ============================================

def run_debate(topic: str, api_key: str):
    topic = topic.strip()

    if not topic:
        raise ValueError("議題が入力されていません。")

    debate_agent = build_debate_agent(api_key)
    initial_state = DebateState(topic=topic)

    return debate_agent.invoke(initial_state)
