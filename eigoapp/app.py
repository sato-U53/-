import streamlit as st
import pandas as pd
import random
import os
import time
import streamlit.components.v1 as components

# =====================================
# ページ設定
# =====================================
st.set_page_config(page_title="英単語テスト", layout="centered")

def keyboard_and_audio_handler():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        let isProcessing = false; // 連続動作防止フラグ
        const keyStatus = {};    // キーの押し下げ状態管理

        function speak(text) {
            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel(); // 前の音声を止めて即座に次を流す
            }
            const uttr = new SpeechSynthesisUtterance(text);
            uttr.lang = 'en-US';
            uttr.rate = 1.0;
            window.speechSynthesis.speak(uttr);
        }

        function pressButton(label) {
            if (isProcessing) return;
            isProcessing = true;
            
            const buttons = Array.from(doc.querySelectorAll('button'));
            const target = buttons.find(btn => {
                const text = btn.innerText || "";
                if (['〇', '△', '×'].includes(label)) return text.trim() === label;
                return text.includes(label);
            });
            
            if (target) {
                target.click();
            }
            
            // 0.5秒間は入力を受け付けない（連打・長押し対策）
            setTimeout(() => { isProcessing = false; }, 500);
        }

        doc.onkeydown = function(e) {
            const key = e.key.toLowerCase();
            if (keyStatus[key]) return; // 押しっぱなしによる連続発火を防止
            keyStatus[key] = true;

            if (key === 'p') {
                const wordElement = doc.querySelector('.word-text-main');
                if (wordElement) speak(wordElement.innerText);
            }
            if (key === 'o') pressButton('👁️');
            if (key === 'k') pressButton('〇');
            if (key === 'l') pressButton('△');
            if (key === ';') pressButton('×');
        };

        doc.onkeyup = function(e) {
            const key = e.key.toLowerCase();
            keyStatus[key] = false; // 指を離したらリセット
        };

        // ボタンのクリックイベントを奪取して誤動作を防ぐ
        setInterval(() => {
            const buttons = Array.from(doc.querySelectorAll('button'));
            buttons.forEach(btn => {
                if (btn.innerText.includes('🔊') && !btn.dataset.hooked) {
                    btn.onclick = (e) => {
                        e.preventDefault();
                        const word = doc.querySelector('.word-text-main').innerText;
                        speak(word);
                    };
                    btn.dataset.hooked = "true";
                }
            });
        }, 500);
        </script>
        """,
        height=0
    )

# =====================================
# ブラウザ側で音声を鳴らすためのJSコンポーネント
# =====================================
def keyboard_and_audio_handler():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        
        // 音声再生関数 (Web Speech API)
        function speak(text) {
            const uttr = new SpeechSynthesisUtterance(text);
            uttr.lang = 'en-US';
            uttr.rate = 1.0;
            window.speechSynthesis.speak(uttr);
        }

        function pressButton(label) {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const target = buttons.find(btn => {
                const text = btn.innerText || "";
                if (['〇', '△', '×'].includes(label)) return text.trim() === label;
                return text.includes(label);
            });
            if (target) target.click();
        }

        // キーボードイベント
        doc.onkeydown = function(e) {
            const key = e.key.toLowerCase();
            if (key === 'p') {
                // Pキーで単語を読み上げ (Pythonを介さずJSで実行)
                const wordElement = doc.querySelector('.word-text-main');
                if (wordElement) speak(wordElement.innerText);
            }
            if (key === 'o') pressButton('👁️');
            if (key === 'k') pressButton('〇');
            if (key === 'l') pressButton('△');
            if (key === ';') pressButton('×');
        };

        // Streamlitのボタンをクリックした時にJS側で音声を出すためのフック
        // 「🔊 音声」というテキストが含まれるボタンを探してイベントを奪う
        setInterval(() => {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const audioBtn = buttons.find(btn => btn.innerText.includes('🔊'));
            if (audioBtn && !audioBtn.dataset.listenerAdded) {
                audioBtn.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const word = doc.querySelector('.word-text-main').innerText;
                    speak(word);
                };
                audioBtn.dataset.listenerAdded = "true";
            }
        }, 500);
        </script>
        """,
        height=0
    )

# =====================================
# CSS (ガタつきを徹底排除)
# =====================================
st.markdown(
    """
<style>
/* 高さを完全に固定 */
.word-box { 
    background-color: #f0f2f6; 
    padding: 30px; 
    border-radius: 15px; 
    text-align: center; 
    margin-bottom: 10px; 
    border: 2px solid #ddd;
    height: 140px; /* min-heightではなくheightで固定 */
    display: flex;
    align-items: center;
    justify-content: center;
}
.word-text-main { font-size: 2.5rem; font-weight: bold; margin: 0; }
.ans-text-main { font-size: 1.8rem; font-weight: bold; color: #1565c0; margin: 0; }

.hint-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; color: #856404; height: 60px; overflow: hidden; }
.stButton>button { height: 3.2em; font-size: 18px; border-radius: 10px; width: 100%; font-weight: bold; }

.timer-text { font-size: 1.6rem; font-weight: bold; color: #e63946; text-align: center; }
.grid-item { background: #f8f9fa; border: 1px solid #e5e7eb; padding: 10px; border-radius: 10px; margin-bottom: 5px; }

/* Streamlit特有の余白を削る */
.block-container { padding-top: 2rem !important; }
</style>
""",
    unsafe_allow_html=True
)

# =====================================
# セッション状態の初期化
# =====================================
if "status" not in st.session_state:
    st.session_state.status = "setting"
    st.session_state.results = {"〇": [], "△": [], "×": []}
    st.session_state.history = []

# =====================================
# 設定画面
# =====================================
if st.session_state.status == "setting":
    st.title("📚 単語テスト設定")
    book_options = {
        "ターゲット1900": "taget1900(6).csv", "ターゲット1400": "target1400.csv",
        "ターゲット1200": "target1200.csv", "ターゲット1000": "target1000.csv",
        "システム英単語": "sis-tan.csv", "LEAP(新)": "leap.csv",
        "LEAP(旧)": "leaped.csv", "速読英単語[必修編]": "sokutan2.csv","速読英単語[入門編]": "sokutan1.csv",
        "速読英熟語": "sokuzyuku.csv", "いろはにほへと": "いろはに.csv",
    }
    selected_book_name = st.selectbox("1: 本を選ぶ", list(book_options.keys()))
    csv_filename = book_options[selected_book_name]

    col1, col2 = st.columns(2)
    start_no = col1.number_input("開始番号", value=1, min_value=1)
    end_no = col2.number_input("終了番号", value=100, min_value=1)

    if st.button("テスト開始！"):
        try:
            current_dir = os.path.dirname(__file__)
            csv_path = os.path.join(current_dir, csv_filename)
            df = pd.read_csv(csv_path, names=["no", "english", "japanese", "hint"])
            df["hint"] = df["hint"].fillna("").astype(str).str.strip()
            mask = (df["no"] >= start_no) & (df["no"] <= end_no)
            target_words = df.loc[mask].to_dict("records")

            if not target_words:
                st.error("指定範囲に単語が見つかりません。")
            else:
                st.session_state.test_list = random.sample(target_words, len(target_words))
                st.session_state.current_idx = 0
                st.session_state.show_ans = False
                st.session_state.show_hint = False
                st.session_state.results = {"〇": [], "△": [], "×": []}
                st.session_state.history = []
                st.session_state.start_time = time.time()
                st.session_state.status = "testing"
                st.rerun()
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

# =====================================
# テスト画面
# =====================================
elif st.session_state.status == "testing":
    keyboard_and_audio_handler() # JSハンドラーを起動
    
    total_q = len(st.session_state.test_list)
    idx = st.session_state.current_idx
    q = st.session_state.test_list[idx]

    t_col1, t_col2 = st.columns([2, 1])
    t_col1.write(f"**Progress: {idx + 1} / {total_q}**")
    elapsed = int(time.time() - st.session_state.start_time)
    t_col2.markdown(f"<div class='timer-text'>⏳ {elapsed}s</div>", unsafe_allow_html=True)
    st.progress((idx + 1) / total_q)

    hint_val = str(q.get("hint", "")).strip()
    has_hint = (hint_val != "" and hint_val.lower() != "nan")

    col_main, col_ctrl = st.columns([7, 3])

    with col_main:
        # JSから値を取得しやすいようにclass 'word-text-main' を付与
        st.markdown(f"<div class='word-box'><h1 class='word-text-main'>{q['english']}</h1></div>", unsafe_allow_html=True)
        
        # ヒントエリアの高さを固定
        if st.session_state.show_hint and has_hint:
            st.markdown(f"<div class='hint-box'>{hint_val}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='hint-box' style='background:transparent; border:none;'></div>", unsafe_allow_html=True)
        
        # 答えエリアの高さを固定
        if st.session_state.show_ans:
            st.markdown(f"<div class='word-box' style='background-color:#e3f2fd;'><h2 class='ans-text-main'>{q['japanese']}</h2></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='word-box' style='background:transparent; border:none;'></div>", unsafe_allow_html=True)

    with col_ctrl:
        # このボタンはJS側でクリックイベントを横取りするので、Pythonの再実行は走りません
        st.button("🔊 音声")
        
        if not st.session_state.show_ans:
            if st.button("👁️ 答え", type="primary"):
                st.session_state.show_ans = True
                st.rerun()
        
        if has_hint and not st.session_state.show_hint:
            if st.button("💡 ヒント"):
                st.session_state.show_hint = True
                st.rerun()

        st.write("---")
        c1, c2, c3 = st.columns(3)
        if c1.button("〇"):
            st.session_state.history.append("〇")
            st.session_state.results["〇"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()
        if c2.button("△"):
            st.session_state.history.append("△")
            st.session_state.results["△"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()
        if c3.button("×"):
            st.session_state.history.append("×")
            st.session_state.results["×"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()

        st.write("---")
        if idx > 0 and st.button("⬅️ 戻る"):
            prev = st.session_state.history.pop()
            st.session_state.results[prev].pop()
            st.session_state.current_idx -= 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            st.rerun()
        
        if st.button("中止"):
            st.session_state.status = "result"
            st.rerun()

# =====================================
# 結果画面
# =====================================
elif st.session_state.status == "result":
    st.title("📊 結果報告")
    res = st.session_state.results
    total = sum(len(v) for v in res.values())
    
    if total > 0:
        acc = (len(res["〇"]) / total) * 100
        st.metric("正答率", f"{acc:.1f}%")
        cols = st.columns(3)
        cols[0].info(f"〇: {len(res['〇'])}")
        cols[1].warning(f"△: {len(res['△'])}")
        cols[2].error(f"×: {len(res['×'])}")

    st.write("---")
    cl, cr = st.columns(2)
    with cl:
        st.subheader("△ (復習)")
        for i in res["△"]: st.markdown(f"<div class='grid-item'>{i['english']} : {i['japanese']}</div>", unsafe_allow_html=True)
    with cr:
        st.subheader("× (要練習)")
        for i in res["×"]: st.markdown(f"<div class='grid-item'>{i['english']} : {i['japanese']}</div>", unsafe_allow_html=True)

    st.write("---")
    retry = res["△"] + res["×"]
    if retry and st.button("🔄 不安な単語を再テスト", type="primary"):
        st.session_state.test_list = random.sample(retry, len(retry))
        st.session_state.current_idx = 0
        st.session_state.results = {"〇": [], "△": [], "×": []}
        st.session_state.history = []
        st.session_state.start_time = time.time()
        st.session_state.status = "testing"
        st.rerun()
    if st.button("🏠 戻る"):
        st.session_state.clear()
        st.rerun()