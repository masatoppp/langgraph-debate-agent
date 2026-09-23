import streamlit as st


# ============================================
# Streamlit 基本設定
# ============================================

st.set_page_config(
    page_title="Debate Agent",
    layout="wide"
)


# ============================================
# API Key
# ============================================

st.sidebar.header("API設定")

api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="入力したAPI Keyは、このアプリの実行にのみ使用します。"
).strip()

if api_key:
    st.sidebar.success("API Keyを受け付けました。")
    st.sidebar.caption("有効性は討論開始時に確認されます。")

st.sidebar.caption(
    "API Keyはこのアプリのファイルには保存しません。"
)
st.sidebar.caption(
    "OpenAI APIの利用料金は、入力したAPI Keyのアカウントに発生します。"
)


# ============================================
# 画面上部
# ============================================

st.title("Debate Agent")

st.write(
    "複数の立場が合理的に成立する、日常的で比較可能なテーマを入力してください。"
)

st.caption(
    "例：犬派 vs 猫派、紙の本 vs 電子書籍、"
    "書籍から学ぶ vs コードを書きながら学ぶ など。"
)

st.caption(
    "客観的に答えが一意に決まる質問や、"
    "政治・宗教・戦争・差別などの強い思想的対立を含むテーマは対象外です。"
)

st.caption(
    "Debaterには「分析型」と「実践型」の異なる討論アプローチを割り当てます。"
    "両者に能力差を設けるものではありません。"
)


# ============================================
# 議題入力
# ============================================

topic = st.text_input(
    "議題を入力してください",
    placeholder="例：犬派 vs 猫派"
).strip()

start_button = st.button("討論開始")


# ============================================
# 実行
# ============================================

if start_button:
    if not api_key:
        st.warning("OpenAI API Keyを入力してください。")

    elif not topic:
        st.warning("議題を入力してください。")

    else:
        try:
            # import時にはAPI Keyを要求せず、
            # 実行時にrun_debate(topic, api_key)へ渡す
            from debate_agent import run_debate

            with st.spinner("討論を実行しています..."):
                result = run_debate(topic, api_key)

        except Exception as exc:
            st.error(
                "討論の実行中にエラーが発生しました。"
                "API Key、通信状態、API利用状況などを確認してください。"
            )
            st.caption(f"エラー種別: {type(exc).__name__}")
            st.stop()

        category = result["validation_category"]

        # ----------------------------------------
        # 議論可能なテーマ
        # ----------------------------------------
        if category == "VALID_DEBATE":

            st.subheader("議題")
            st.write(result["normalized_topic"])

            st.divider()

            # ------------------------------------
            # 討論履歴
            # ------------------------------------
            st.subheader("Debate")

            for message in result["debate_history"]:
                if message.startswith("Debater A:\n"):
                    label = "Debater A"
                    body = message.removeprefix("Debater A:\n")

                elif message.startswith("Debater B:\n"):
                    label = "Debater B"
                    body = message.removeprefix("Debater B:\n")

                else:
                    label = "Debater"
                    body = message

                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.write(body)

            st.divider()

            # ------------------------------------
            # Persona
            # ------------------------------------
            persona_a = result["persona_a"]
            persona_b = result["persona_b"]

            st.subheader("今回のPersona")
            st.caption(
                "「分析型 / 実践型」は能力差ではなく、"
                "主張を組み立てるアプローチの違いを表します。"
            )

            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    st.markdown("### Debater A")
                    st.markdown(
                        f"**討論アプローチ:** {persona_a.style_type}"
                    )
                    st.write(f"立場: {persona_a.position}")
                    st.write(f"人物像: {persona_a.personality}")

            with col2:
                with st.container(border=True):
                    st.markdown("### Debater B")
                    st.markdown(
                        f"**討論アプローチ:** {persona_b.style_type}"
                    )
                    st.write(f"立場: {persona_b.position}")
                    st.write(f"人物像: {persona_b.personality}")

            st.divider()

            # ------------------------------------
            # Judge
            # ------------------------------------
            judgment = result["judgment"]
            winner = judgment["winner"]

            st.subheader("Judge Result")

            if winner == "A":
                st.success("Debater A の主張がより説得的")
                st.write(f"主張: {persona_a.position}")

            elif winner == "B":
                st.success("Debater B の主張がより説得的")
                st.write(f"主張: {persona_b.position}")

            else:
                st.info("両者の説得力は同程度")

            st.markdown("### 判定理由")
            st.write(judgment["reason"])

            strengths_col1, strengths_col2 = st.columns(2)

            with strengths_col1:
                st.markdown("### Debater A の良かった点")
                st.write(judgment["strengths_a"])

            with strengths_col2:
                st.markdown("### Debater B の良かった点")
                st.write(judgment["strengths_b"])

        # ----------------------------------------
        # 客観的事実など
        # ----------------------------------------
        elif category == "NOT_DEBATABLE":
            st.warning(
                "この入力は、客観的な事実などによって答えが決まるため、"
                "討論テーマとしては扱いません。"
            )

            st.write(
                f"理由: {result['validation_reason']}"
            )

        # ----------------------------------------
        # 対象外テーマ
        # ----------------------------------------
        elif category == "RESTRICTED_TOPIC":
            st.error(
                "このエージェントでは、政治・宗教・戦争・差別など、"
                "強い思想的対立を含むテーマは討論対象としていません。"
            )

            st.write(
                f"理由: {result['validation_reason']}"
            )
