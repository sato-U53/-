import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import base64
import uuid
import time
import streamlit.components.v1 as components

# =====================================
# ページ設定
# =====================================
st.set_page_config(page_title="英単語テスト", layout="centered")

# =====================================
# 音声再生
# =====================================
def speak(text: str):
   filename = f"temp_{uuid.uuid4().hex}.mp3"
   try:
       tts = gTTS(text=text, lang="en")
       tts.save(filename)
       with open(filename, "rb") as f:
           b64 = base64.b64encode(f.read()).decode("utf-8")
       html = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
       st.markdown(html, unsafe_allow_html=True)
   except Exception as e:
       st.error(f"音声生成エラー: {e}")
   finally:
       if os.path.exists(filename):
           try: os.remove(filename)
           except: pass

# =====================================
# 強力なキーボード操作用JavaScript
# =====================================
def keyboard_handler():
   components.html(
       """
       <script>
       const doc = window.parent.document;

       function pressButton(label) {
           const buttons = Array.from(doc.querySelectorAll('button'));
           const target = buttons.find(btn => {
               const text = btn.innerText || "";
               if (['〇', '△', '×'].includes(label)) {
                   return text.trim() === label;
               }
               return text.includes(label);
           });
           if (target) {
               target.click();
           }
       }

       doc.onkeydown = function(e) {
           const key = e.key.toLowerCase();
           if (key === 'p') pressButton('🔊');
           if (key === 'o') pressButton('👁️');
           if (key === 'k') pressButton('〇');
           if (key === 'l') pressButton('△');
           if (key === ';') pressButton('×');
       };
       </script>
       """,
       height=0
   )

# =====================================
# CSS（スマホ横並び対応版）
# =====================================
st.markdown(
   """
<style>
.word-box { background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 10px; border: 2px solid #ddd; }
.hint-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; color: #856404; }
.stButton>button { height: 3.2em; font-size: 18px; border-radius: 10px; width: 100%; font-weight: bold; }
.answer-spacer { height: 100px; }
.timer-text { font-size: 1.6rem; font-weight: bold; color: #e63946; text-align: center; }
.grid-item { background: #f8f9fa; border: 1px solid #e5e7eb; padding: 10px; border-radius: 10px; margin-bottom: 5px; }

/* ===== スマホで判定ボタンを横並びにする魔法のCSS ===== */
[data-testid="column"]:has(button[kind="secondary"]):has(span:contains("〇")),
[data-testid="column"]:has(button[kind="secondary"]):has(span:contains("△")),
[data-testid="column"]:has(button[kind="secondary"]):has(span:contains("×")) {
   flex: 1 !important;
   min-width: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(button:contains("〇")) {
   display: flex !important;
   flex-direction: row !important;
   flex-wrap: nowrap !important;
   gap: 8px !important;
}

@media (max-width: 768px) {
   .word-box { padding: 16px; }
   .word-box h1 { font-size: 1.8rem; }
   .stButton>button { height: 2.8em; font-size: 16px; }
   .answer-spacer { height: 40px; }
}
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
       "システム英単語": "sis-tan.csv", "LEAP": "leap.csv",
       "LEAP(旧)": "leaped.csv", "速読英単語必修編": "sokutan2.csv",
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
   keyboard_handler()

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
       st.markdown(f"<div class='word-box'><h1>{q['english']}</h1></div>", unsafe_allow_html=True)
       if st.session_state.show_hint and has_hint:
           st.markdown(f"<div class='hint-box'>{hint_val}</div>", unsafe_allow_html=True)
       if st.session_state.show_ans:
           st.markdown(f"<div class='word-box' style='background-color:#e3f2fd;'><h2>{q['japanese']}</h2></div>", unsafe_allow_html=True)
       else:
           st.markdown("<div class='answer-spacer'></div>", unsafe_allow_html=True)

   with col_ctrl:
       st.button("🔊 音声 (I)", on_click=lambda: speak(q["english"]))
       if not st.session_state.show_ans:
           if st.button("👁️ 答え (O)", type="primary"):
               st.session_state.show_ans = True
               st.rerun()
       if has_hint and not st.session_state.show_hint:
           if st.button("💡 ヒント"):
               st.session_state.show_hint = True
               st.rerun()

       st.write("---")
       # ★ ここが横並びになる部分
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
