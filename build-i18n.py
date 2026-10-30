#!/usr/bin/env python3
"""Generate the English (en/) and Japanese (ja/) game pages from the Chinese index.html.

index.html is the single source of truth. After editing it, run:

    python3 build-i18n.py

The script swaps the <!--SEO--> head block and the <!--ABOUT--> intro panel wholesale,
then replaces every UI string listed in STRINGS. Each source string must still exist in
index.html, so a renamed or reworded string fails loudly instead of silently staying Chinese.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://tesla-roadster.sectools.tw'

# (Chinese source, English, Japanese). Longer strings are applied first.
STRINGS = [
    # --- static HTML ---
    ('title="畫質切換"', 'title="Graphics quality"', 'title="画質切替"'),
    ('title="靜音 (M)" aria-label="靜音"', 'title="Mute (M)" aria-label="Mute"', 'title="ミュート (M)" aria-label="ミュート"'),
    ('title="暫停 (P)" aria-label="暫停"', 'title="Pause (P)" aria-label="Pause"', 'title="一時停止 (P)" aria-label="一時停止"'),
    ('aria-label="關閉"', 'aria-label="Close"', 'aria-label="閉じる"'),
    ('>點擊畫面或按任意鍵略過<', '>Tap or press any key to skip<', '>タップまたは任意のキーでスキップ<'),
    ('>成就解鎖<', '>ACHIEVEMENT<', '>実績解除<'),
    ('<span class="zh">極速電能狂飆</span>', '<span class="zh">ELECTRIC HYPERCAR RACING</span>', '<span class="zh">電動スーパーカー・レース</span>'),
    ('<span><kbd>←</kbd><kbd>→</kbd>變換車道</span><span><kbd>↑</kbd>噴射飛行</span><span><kbd>Space</kbd>BOOST</span><span><kbd>↓</kbd>煞車</span><span>空中按 <kbd>←</kbd><kbd>→</kbd> 翻滾</span>',
     '<span><kbd>←</kbd><kbd>→</kbd>Change lanes</span><span><kbd>↑</kbd>Thruster flight</span><span><kbd>Space</kbd>BOOST</span><span><kbd>↓</kbd>Brake</span><span><kbd>←</kbd><kbd>→</kbd> in the air to roll</span>',
     '<span><kbd>←</kbd><kbd>→</kbd>車線変更</span><span><kbd>↑</kbd>ジェット飛行</span><span><kbd>Space</kbd>BOOST</span><span><kbd>↓</kbd>ブレーキ</span><span>空中で <kbd>←</kbd><kbd>→</kbd> 回転</span>'),
    ('<span>按住螢幕左/右半邊轉向</span><span>JET 按鈕噴射飛行</span><span>BOOST 按鈕加速</span><span>空中轉向可翻滾</span>',
     '<span>Hold left / right half to steer</span><span>JET button to fly</span><span>BOOST button to speed up</span><span>Steer in the air to roll</span>',
     '<span>画面の左右を長押しで操作</span><span>JET ボタンで飛行</span><span>BOOST ボタンで加速</span><span>空中で操作すると回転</span>'),
    ('>載入中…<', '>Loading…<', '>読み込み中…<'),
    ('>更多工具 Sectools.tw<', '>More tools: Sectools.tw<', '>便利ツール Sectools.tw<'),
    ('>分享遊戲<', '>Share<', '>シェア<'),
    ('>遊戲介紹<', '>About<', '>ゲーム紹介<'),
    ('id="achvBtn">成就<', 'id="achvBtn">Achievements<', 'id="achvBtn">実績<'),
    ('<a class="lbtn" href="guide.html">攻略</a>', '<a class="lbtn" href="en/guide.html">Guide</a>', '<a class="lbtn" href="ja/guide.html">攻略</a>'),
    ('>非官方粉絲作品 · 擦身超車、飛躍跳台、空中翻滾都能加分<', '>Unofficial fan game · near misses, ramp jumps and air rolls all score points<', '>非公式ファンゲーム · ニアミス、ジャンプ、空中回転でスコアアップ<'),
    ('<p class="reason">暫停中</p><button class="btn" id="resumeBtn">繼續</button>', '<p class="reason">Paused</p><button class="btn" id="resumeBtn">Resume</button>', '<p class="reason">一時停止中</p><button class="btn" id="resumeBtn">再開</button>'),
    ('<p class="reason" id="reason">撞車了！</p>', '<p class="reason" id="reason">You crashed!</p>', '<p class="reason" id="reason">クラッシュ！</p>'),
    ('>SCORE 分數<', '>SCORE<', '>SCORE スコア<'),
    ('<div class="l">距離</div>', '<div class="l">Distance</div>', '<div class="l">距離</div>'),
    ('<div class="l">極速 km/h</div>', '<div class="l">Top km/h</div>', '<div class="l">最高 km/h</div>'),
    ('<div class="l">擦身</div>', '<div class="l">Near misses</div>', '<div class="l">ニアミス</div>'),
    ('>再來一次<', '>Play again<', '>もう一度<'),
    ('>分享成績<', '>Share score<', '>スコアをシェア<'),
    ('>存成績圖<', '>Save score image<', '>画像を保存<'),
    ('<b>喜歡這個遊戲嗎？</b><span>Sectools.tw 還有更多免費實用小工具，免安裝、打開就能用</span>',
     '<b>Enjoyed the game?</b><span>Sectools.tw has more free, no-install tools you can use right in your browser</span>',
     '<b>このゲーム、気に入りましたか？</b><span>Sectools.tw にはインストール不要の無料ツールがたくさんあります</span>'),
    ('>去逛逛 →<', '>Visit →<', '>見てみる →<'),
    ('>本機排行榜 TOP 5<', '>Your top 5 (this device)<', '>この端末の TOP 5<'),
    ('<h2 id="achvTitle">成就</h2>', '<h2 id="achvTitle">Achievements</h2>', '<h2 id="achvTitle">実績</h2>'),
    ('>無法啟動 3D<', '>Unable to start 3D<', '>3D を起動できません<'),
    ('>重新載入<', '>Reload<', '>再読み込み<'),
    ('Roadster Rush 是一款免費 3D 網頁賽車遊戲，需要啟用 JavaScript 才能遊玩。', 'Roadster Rush is a free 3D browser racing game. Please enable JavaScript to play.', 'Roadster Rush は無料の 3D ブラウザレースゲームです。プレイするには JavaScript を有効にしてください。'),
    # --- boot diagnostics ---
    ("'瀏覽器的 3D 加速目前無法使用'", "'3D acceleration is unavailable in this browser'", "'ブラウザの 3D アクセラレーションが使用できません'"),
    ("'你的瀏覽器支援 WebGL，但現在被停用了，通常是「硬體加速」被關掉，或顯示卡被瀏覽器封鎖。<ol>'",
     "'Your browser supports WebGL, but it is currently disabled — usually hardware acceleration is turned off or the GPU is blocklisted.<ol>'",
     "'ブラウザは WebGL に対応していますが、現在無効になっています。多くの場合、ハードウェアアクセラレーションがオフか、GPU がブロックされています。<ol>'"),
    ("'<li>Chrome：開啟 <code>設定 → 系統</code>，打開「<b>可用時使用圖形加速功能</b>」，按「重新啟動」</li>'",
     "'<li>Chrome: open <code>Settings → System</code>, turn on “<b>Use graphics acceleration when available</b>”, then Relaunch</li>'",
     "'<li>Chrome：<code>設定 → システム</code> で「<b>グラフィック アクセラレーションが使用可能な場合は使用する</b>」をオンにして再起動</li>'"),
    ("'<li>在網址列輸入 <code>chrome://gpu</code>，看 WebGL 那一行是否顯示 Hardware accelerated</li>'",
     "'<li>Open <code>chrome://gpu</code> and check that WebGL says Hardware accelerated</li>'",
     "'<li>アドレスバーに <code>chrome://gpu</code> と入力し、WebGL が Hardware accelerated か確認</li>'"),
    ("'<li>更新顯示卡驅動程式，或換 Edge / Safari / Firefox 試試</li></ol>'", "'<li>Update your graphics driver, or try Edge / Safari / Firefox</li></ol>'", "'<li>グラフィックドライバーを更新するか、Edge / Safari / Firefox をお試しください</li></ol>'"),
    ("'遊戲引擎載入失敗'", "'The game engine failed to load'", "'ゲームエンジンの読み込みに失敗しました'"),
    ("'無法從網路下載 3D 引擎（Three.js）。<ol>'", "'Could not download the 3D engine (Three.js).<ol>'", "'3D エンジン（Three.js）をダウンロードできませんでした。<ol>'"),
    ("'<li>確認網路連線正常後重新載入</li>'", "'<li>Check your connection and reload</li>'", "'<li>ネット接続を確認して再読み込み</li>'"),
    ("'<li>若有廣告封鎖或公司防火牆，請允許 <code>cdn.jsdelivr.net</code></li>'", "'<li>If you use an ad blocker or firewall, allow <code>cdn.jsdelivr.net</code></li>'", "'<li>広告ブロッカーやファイアウォールで <code>cdn.jsdelivr.net</code> を許可</li>'"),
    ("'<li>關閉可能干擾的瀏覽器擴充功能後再試</li></ol>'", "'<li>Disable browser extensions that may interfere and try again</li></ol>'", "'<li>干渉する可能性のある拡張機能を無効にして再試行</li></ol>'"),
    ("'詳細錯誤：'", "'Details: '", "'詳細：'"),
    # --- 三寶 tag (canvas) ---
    ("g.font = `900 60px ${ZH}`; g.fillText('三寶', w / 2, h / 2 + 3);",
     "g.font = '44px \"Russo One\",sans-serif'; g.fillText('BAD DRIVER', w / 2, h / 2 + 3, w - 34);",
     "g.font = `900 46px ${ZH}`; g.fillText('危険運転', w / 2, h / 2 + 3, w - 34);"),
    # --- achievements ---
    ("['near', '第一次擦身', '完成一次 NEAR MISS']", "['near', 'First Near Miss', 'Pull off a NEAR MISS']", "['near', '初ニアミス', 'NEAR MISS を1回達成']"),
    ("['combo5', '連擊大師', 'COMBO 達到 ×5']", "['combo5', 'Combo Master', 'Reach a ×5 COMBO']", "['combo5', 'コンボマスター', 'COMBO ×5 を達成']"),
    ("['fly', '起飛！', '用噴射推進器飛起來']", "['fly', 'Liftoff!', 'Fly with the thrusters']", "['fly', 'リフトオフ！', 'ジェットで飛行する']"),
    ("['roll', '空中翻滾', '完成一次 BARREL ROLL']", "['roll', 'Barrel Roller', 'Land a BARREL ROLL']", "['roll', 'バレルロール', 'BARREL ROLL を決める']"),
    ("['over', '飛越車頂', '完成一次 JUMP OVER']", "['over', 'Over the Top', 'JUMP OVER another car']", "['over', '車越え', 'JUMP OVER を達成']"),
    ("['sb10', '三寶剋星', '單局閃過 10 台三寶']", "['sb10', 'Bad Driver Buster', 'Dodge 10 bad drivers in one run']", "['sb10', '危険運転キラー', '1回で危険運転車を10台かわす']"),
    ("['wrong', '死裡逃生', '閃過逆向車']", "['wrong', 'Close Call', 'Dodge a wrong-way driver']", "['wrong', '九死に一生', '逆走車をかわす']"),
    ("['km5', '長途旅行', '單局跑完 5 km']", "['km5', 'Road Trip', 'Drive 5 km in one run']", "['km5', 'ロングドライブ', '1回で 5 km 走る']"),
    ("['speed400', '光速', '時速突破 400 km/h']", "['speed400', 'Light Speed', 'Break 400 km/h']", "['speed400', '光速', '時速 400 km/h 突破']"),
    ("['score20k', '公路之王', '單局拿到 20,000 分']", "['score20k', 'King of the Road', 'Score 20,000 in one run']", "['score20k', '公道の王', '1回で 20,000 点']"),
    ("`成就 ${achv.size}/${ACHV.length}`", "`Achievements ${achv.size}/${ACHV.length}`", "`実績 ${achv.size}/${ACHV.length}`"),
    ("`已解鎖 ${achv.size} / ${ACHV.length}`", "`Unlocked ${achv.size} / ${ACHV.length}`", "`解除済み ${achv.size} / ${ACHV.length}`"),
    # --- first-run hints ---
    ("isTouch ? '按住螢幕左右半邊變換車道' : '用 ← → 變換車道'", "isTouch ? 'Hold the left / right half of the screen to change lanes' : 'Use ← → to change lanes'", "isTouch ? '画面の左右を長押しで車線変更' : '← → で車線変更'"),
    ("'貼著其他車超車 = NEAR MISS 加分'", "'Pass cars closely for NEAR MISS points'", "'他の車スレスレで追い越すと NEAR MISS'"),
    ("isTouch ? '按住左下 JET 飛起來，越過車陣！' : '按住 ↑ 啟動噴射推進器，飛越車陣！'", "isTouch ? 'Hold JET (bottom left) to fly over traffic!' : 'Hold ↑ to fire the thrusters and fly over traffic!'", "isTouch ? '左下の JET 長押しで車列を飛び越えろ！' : '↑ 長押しでジェット噴射、車列を飛び越えろ！'"),
    ("isTouch ? '右下 BOOST 全速衝刺' : '按 SPACE 啟動 BOOST 全速衝刺'", "isTouch ? 'BOOST (bottom right) for full speed' : 'Press SPACE to BOOST'", "isTouch ? '右下の BOOST で全開加速' : 'SPACE で BOOST 全開'"),
    ("'頭頂「三寶」的車特別危險，閃過分數加倍'", "'Cars tagged BAD DRIVER are dangerous — dodging them scores double'", "'「危険運転」の車は要注意、かわすとスコア2倍'"),
    # --- best / unlocks / reasons / popups ---
    ("`最佳紀錄 ${best.toLocaleString()}`", "`Best ${best.toLocaleString()}`", "`ベスト ${best.toLocaleString()}`"),
    ("'解鎖新車色：' + unlocked.map(p => p.name).join('、') + '！'", "'New paint unlocked: ' + unlocked.map(p => p.name).join(', ') + '!'", "'新しいカラー解除：' + unlocked.map(p => p.name).join('、') + '！'"),
    ("popup('NIGHT DRIVE', '夜幕降臨', 'cyan')", "popup('NIGHT DRIVE', 'Night has fallen', 'cyan')", "popup('NIGHT DRIVE', '夜になった', 'cyan')"),
    ("popup('THRUSTERS!', '噴射推進器啟動', 'cyan')", "popup('THRUSTERS!', 'Cold-gas thrusters engaged', 'cyan')", "popup('THRUSTERS!', 'ジェット噴射', 'cyan')"),
    ("crash('落地翻車了！')", "crash('Flipped on landing!')", "crash('着地失敗！')"),
    ("crash('飛出護欄了！')", "crash('Flew off the bridge!')", "crash('ガードレールの外へ！')"),
    ("popup('驚險落地！', '車身歪了，速度降低', 'red')", "popup('SKETCHY LANDING!', 'Crooked touchdown, speed lost', 'red')", "popup('ギリギリ着地！', '車体が傾いて減速', 'red')"),
    ("crash('撞上車了！', c)", "crash('You hit a car!', c)", "crash('車に衝突！', c)"),
    ("label = '閃過逆向車！'", "label = 'DODGED WRONG-WAY!'", "label = '逆走車回避！'"),
    ("label = close ? '極限閃過三寶！' : '閃過三寶'", "label = close ? 'BAD DRIVER — SUPER CLOSE!' : 'DODGED BAD DRIVER'", "label = close ? '危険運転をギリギリ回避！' : '危険運転を回避'"),
    ("popup('逆向車！', '快閃開', 'red')", "popup('WRONG-WAY DRIVER!', 'Get out of the way', 'red')", "popup('逆走車！', 'よけろ！', 'red')"),
    ("popup('三寶出沒！', '小心切入、急煞、蛇行', 'red')", "popup('BAD DRIVERS AHEAD!', 'Watch for cut-ins, brake checks, weaving', 'red')", "popup('危険運転車 出現！', '割り込み・急ブレーキ・蛇行に注意', 'red')"),
    ("popup('三寶切入！', '', 'red')", "popup('CUT-IN!', '', 'red')", "popup('割り込み！', '', 'red')"),
    ("popup('三寶急煞！', '', 'red')", "popup('BRAKE CHECK!', '', 'red')", "popup('急ブレーキ！', '', 'red')"),
    # --- toasts / quality ---
    ("toast('已自動切換為流暢畫質（右上角可切回 HD）')", "toast('Switched to smooth mode (tap HD at the top right to switch back)')", "toast('軽量モードに切り替えました（右上の HD で戻せます）')"),
    ("toast(quality === 'high' ? '高畫質 HD' : '流暢模式 SD')", "toast(quality === 'high' ? 'High quality (HD)' : 'Smooth mode (SD)')", "toast(quality === 'high' ? '高画質 HD' : '軽量モード SD')"),
    ("toast('已複製分享連結！')", "toast('Share link copied!')", "toast('シェア用リンクをコピーしました！')"),
    # --- paints ---
    ("name: '珍珠白'", "name: 'Pearl White'", "name: 'パールホワイト'"),
    ("name: '烈焰紅'", "name: 'Flame Red'", "name: 'フレイムレッド'"),
    ("name: '午夜黑'", "name: 'Midnight Black'", "name: 'ミッドナイトブラック'"),
    ("name: '深海藍'", "name: 'Deep Blue'", "name: 'ディープブルー'"),
    ("name: '香檳金'", "name: 'Champagne Gold'", "name: 'シャンパンゴールド'"),
    ("name: '星際銀'", "name: 'Stellar Silver'", "name: 'ステラシルバー'"),
    ("`${p.name}：最佳紀錄 ${p.need.toLocaleString()} 分解鎖`", "`${p.name}: unlocks at a best score of ${p.need.toLocaleString()}`", "`${p.name}：ベスト ${p.need.toLocaleString()} 点で解除`"),
    ("`${p.name}：最佳紀錄達 ${p.need.toLocaleString()} 分解鎖`", "`${p.name}: reach a best score of ${p.need.toLocaleString()} to unlock`", "`${p.name}：ベスト ${p.need.toLocaleString()} 点で解除`"),
    ("'車色：' + PAINTS[paintIdx].name", "'Paint: ' + PAINTS[paintIdx].name", "'カラー：' + PAINTS[paintIdx].name"),
    # --- score card (canvas) ---
    ("g.fillText('極速電能狂飆', 72, 180)", "g.fillText('Electric Hypercar Racing', 72, 180)", "g.fillText('電動スーパーカー・レース', 72, 180)"),
    ("[r.dist.toFixed(2) + ' km', '距離'], [r.top + ' km/h', '極速'], [String(r.near), '擦身超車']",
     "[r.dist.toFixed(2) + ' km', 'Distance'], [r.top + ' km/h', 'Top speed'], [String(r.near), 'Near misses']",
     "[r.dist.toFixed(2) + ' km', '距離'], [r.top + ' km/h', '最高速度'], [String(r.near), 'ニアミス']"),
    ("g.fillText('你能超越嗎？ tesla-roadster.sectools.tw', W / 2, 1278)", "g.fillText('Can you beat it? tesla-roadster.sectools.tw', W / 2, 1278)", "g.fillText('この記録、超えられる？ tesla-roadster.sectools.tw', W / 2, 1278)"),
    ("g.fillText('更多免費工具 · Sectools.tw', W / 2, 1318)", "g.fillText('More free tools · Sectools.tw', W / 2, 1318)", "g.fillText('便利な無料ツール · Sectools.tw', W / 2, 1318)"),
    # --- share text ---
    ("`我在 Roadster Rush 拿到 ${Math.floor(score).toLocaleString()} 分、跑了 ${((ps - startS) / 1000).toFixed(2)} km！你能超越嗎？🏎️⚡`",
     "`I scored ${Math.floor(score).toLocaleString()} and drove ${((ps - startS) / 1000).toFixed(2)} km in Roadster Rush! Can you beat it? 🏎️⚡`",
     "`Roadster Rush で ${Math.floor(score).toLocaleString()} 点、${((ps - startS) / 1000).toFixed(2)} km 走ったよ！超えられる？🏎️⚡`"),
    ("'Roadster Rush 極速電能狂飆：開 Roadster 在夕陽海岸大橋上狂飆！🏎️⚡'", "'Roadster Rush: race an electric hypercar across a sunset ocean bridge! 🏎️⚡'", "'Roadster Rush：電動スーパーカーで夕暮れの海上橋を爆走！🏎️⚡'"),
    ("sb.textContent = 'START 出發'", "sb.textContent = 'START'", "sb.textContent = 'START スタート'"),
]

SEO = {
    'en': {
        'title': 'Roadster Rush – Free 3D Electric Hypercar Racing Game in Your Browser',
        'desc': 'Free 3D browser racing game. Drive a Tesla Roadster–inspired electric hypercar across a sunset ocean bridge: fly over traffic with cold-gas thrusters, chain near-miss combos, hit ramps and barrel rolls. No download — play on mobile or PC.',
        'keywords': 'Roadster game, Tesla Roadster game, racing game, browser game, free online game, 3D racing game, mobile racing game, electric car game, endless racer, Roadster Rush',
        'og_title': 'Roadster Rush – Electric Hypercar Racing 🏎️⚡',
        'og_desc': 'Race across a sunset ocean bridge in 3D! Near misses, ramp jumps, barrel rolls and thruster flights. How far can you go? Free, no install.',
        'og_alt': 'Roadster Rush gameplay: a white electric sports car on a sunset ocean bridge',
        'locale': 'en_US', 'in_lang': 'en', 'currency': 'USD', 'name': 'Roadster Rush',
        'faq': [
            ('Is Roadster Rush free?', 'Yes. It is completely free — open the page and play, no sign-up or download.'),
            ('Can I play on my phone?', 'Yes. Hold the left or right half of the screen to steer, use JET (bottom left) to fly and BOOST (bottom right) to speed up. On PC use the arrow keys and Space.'),
            ('How do I get a high score?', 'Pass cars closely for NEAR MISS points and chain them into combos. Ramp jumps, barrel rolls, thruster flights over traffic and dodging bad drivers all give big bonuses.'),
            ('Is this an official Tesla game?', 'No. It is an unofficial fan game and is not affiliated with Tesla, Inc.'),
        ],
    },
    'ja': {
        'title': 'Roadster Rush｜無料3Dブラウザレースゲーム（電動スーパーカー）',
        'desc': '無料で遊べる3Dブラウザレースゲーム。テスラ・ロードスター風の電動スーパーカーで夕暮れの海上橋を爆走！ジェット噴射で車列を飛び越え、ニアミスでコンボ、ジャンプ台でバレルロール。ダウンロード不要、スマホ・PCで今すぐプレイ。',
        'keywords': 'ロードスター ゲーム,テスラ ゲーム,レースゲーム,ブラウザゲーム,無料ゲーム,3Dレースゲーム,スマホ レースゲーム,電気自動車 ゲーム,Roadster Rush',
        'og_title': 'Roadster Rush – 電動スーパーカー・レース 🏎️⚡',
        'og_desc': '夕暮れの海上橋を3Dで爆走！ニアミス、ジャンプ、バレルロール、ジェット飛行。どこまで走れる？無料・インストール不要。',
        'og_alt': 'Roadster Rush のゲーム画面：夕暮れの海上橋を走る白い電動スポーツカー',
        'locale': 'ja_JP', 'in_lang': 'ja', 'currency': 'JPY', 'name': 'Roadster Rush',
        'faq': [
            ('Roadster Rush は無料ですか？', 'はい、完全無料です。登録もダウンロードも不要で、ページを開けばすぐ遊べます。'),
            ('スマホで遊べますか？', 'はい。画面の左右を長押しで操作、左下の JET で飛行、右下の BOOST で加速します。PC は矢印キーとスペースキーで操作します。'),
            ('ハイスコアのコツは？', '他の車スレスレで追い越す NEAR MISS をつなげてコンボ倍率を上げましょう。ジャンプ台、バレルロール、ジェット飛行での車越え、危険運転車の回避も高得点です。'),
            ('テスラ公式のゲームですか？', 'いいえ。非公式のファンゲームで、Tesla, Inc. とは関係ありません。'),
        ],
    },
}

ABOUT = {
    'en': '''
    <h2 id="aboutTitle">About Roadster Rush</h2>
    <p><strong>Roadster Rush</strong> is a free 3D racing game that runs in your browser. You drive a white electric hypercar (inspired by the Tesla Roadster) across an ocean bridge at sunset — dodging traffic, passing cars by inches and launching off ramps for the highest score. No app to install: it works on phones and computers.</p>
    <h3>How to play</h3>
    <ul>
      <li><b>PC:</b> ← → (or A / D) to change lanes, Space or Shift to BOOST, ↑ / W to fire the thrusters, ↓ to brake, P to pause, M to mute.</li>
      <li><b>Mobile:</b> hold the left or right half of the screen to steer. JET (bottom left) fires the thrusters, BOOST (bottom right) speeds you up. The car accelerates by itself.</li>
      <li><b>Thrusters:</b> a nod to the new Roadster's cold-gas thrusters — hold to lift off and fly over whole lines of traffic, sliding left and right in the air. Fuel refills on the ground and with every near miss.</li>
      <li><b>In the air:</b> after an orange ramp, press left / right to barrel roll. The car straightens itself just before touchdown.</li>
    </ul>
    <h3>Scoring tips</h3>
    <ul>
      <li><b>NEAR MISS:</b> pass other cars closely at speed. The closer, the more points (SUPER CLOSE) — and it refills BOOST.</li>
      <li><b>COMBO:</b> chain stunts to build a multiplier that applies to every bonus. Scraping the barrier breaks it.</li>
      <li><b>Ramp stunts:</b> air time, JUMP OVER and BARREL ROLL all pay big.</li>
      <li><b>Bad drivers:</b> the farther you go, the more cars tagged BAD DRIVER appear — slowpokes in the fast lane, sudden cut-ins, brake checks, weaving and even wrong-way drivers. Dodging them scores double.</li>
      <li><b>Boost pads:</b> drive over the blue arrows to refill BOOST instantly.</li>
    </ul>
    <h3>Features</h3>
    <ul>
      <li>Real-time 3D: sunset sky, reflective sea, palm-lined coast, city skyline and bloom lighting.</li>
      <li>Day-to-night cycle: the sun sets as you drive until you're cruising under the stars with headlights on, backed by a procedurally generated synthwave soundtrack.</li>
      <li>Opening stunt inspired by the 2026 Roadster reveal: a curling wall ramp and a 180° roll landing.</li>
      <li>Smart traffic that changes lanes; difficulty and top speed rise gradually with distance.</li>
      <li>Top speed around 330 km/h, over 450 km/h with BOOST, with speed lines and light trails.</li>
      <li>Taiwanese highway scenery: freeway guide signs, speed-limit and speed-camera signs.</li>
      <li>Unlockable paint colours, 10 achievements, a local top 5 and shareable score cards.</li>
    </ul>
    <h3>FAQ</h3>
    <dl>
      <dt>Is it free? Do I need an account?</dt><dd>Completely free, no account or download needed.</dd>
      <dt>It's laggy on my phone.</dt><dd>The game switches to smooth mode automatically on slower devices. You can also toggle HD / SD at the top right.</dd>
      <dt>Is this an official Tesla game?</dt><dd>No. It is an unofficial fan game, not affiliated with Tesla, Inc.</dd>
    </dl>
    <p class="more">Want a higher score? Read the full <a href="en/guide.html">Roadster Rush guide: scoring, bad drivers and thruster tips</a>.<br>For more free tools, visit <a href="https://sectools.tw" target="_blank" rel="noopener">Sectools.tw</a>.</p>
''',
    'ja': '''
    <h2 id="aboutTitle">Roadster Rush について</h2>
    <p><strong>Roadster Rush</strong> はブラウザで遊べる無料の 3D レースゲームです。テスラ・ロードスター風の白い電動スーパーカーを操り、夕暮れの海上橋を疾走。車の流れをかわし、スレスレで追い越し、ジャンプ台から飛び出してハイスコアを狙いましょう。アプリのインストールは不要で、スマホでも PC でも遊べます。</p>
    <h3>遊び方</h3>
    <ul>
      <li><b>PC：</b>← →（または A / D）で車線変更、Space か Shift で BOOST、↑ / W でジェット噴射、↓ でブレーキ、P で一時停止、M でミュート。</li>
      <li><b>スマホ：</b>画面の左半分または右半分を長押しで操作。左下の JET でジェット噴射、右下の BOOST で加速。車は自動で加速します。</li>
      <li><b>ジェット噴射：</b>新型ロードスターのコールドガス・スラスターへのオマージュ。長押しで車体が浮き上がり、車列をまるごと飛び越えられます。空中では左右に移動可能。燃料は地上で自動回復し、ニアミスでも補充されます。</li>
      <li><b>空中：</b>オレンジのジャンプ台から飛んだら、左右でバレルロール。着地直前に車体は自動で水平に戻ります。</li>
    </ul>
    <h3>スコアのコツ</h3>
    <ul>
      <li><b>NEAR MISS：</b>高速で他の車スレスレを追い越すと加点。近いほど高得点（SUPER CLOSE）で、BOOST も回復します。</li>
      <li><b>COMBO：</b>技を連続で決めると倍率が上がり、すべてのボーナスに掛かります。ガードレールに擦るとリセット。</li>
      <li><b>ジャンプ台：</b>滞空時間、JUMP OVER（車越え）、BARREL ROLL は大量得点。</li>
      <li><b>危険運転車：</b>走るほど「危険運転」マークの車が増えます。追い越し車線の低速車、急な割り込み、急ブレーキ、蛇行、さらには逆走車まで！かわすとスコア2倍です。</li>
      <li><b>ブーストパッド：</b>路面の青い矢印を踏むと BOOST が即回復。</li>
    </ul>
    <h3>特徴</h3>
    <ul>
      <li>リアルタイム 3D：夕焼け空、反射する海、ヤシの木の海岸、街のスカイライン、ブルーム効果。</li>
      <li>昼から夜へ：走るほど日が沈み、やがて星空の下をヘッドライトで疾走。リアルタイム生成のシンセウェイヴ BGM 付き。</li>
      <li>2026 年のロードスター発表会を再現したオープニング：カールする壁ランプから 180° 回転して着地。</li>
      <li>車線変更する賢い交通。距離に応じて難易度と最高速度が少しずつ上昇。</li>
      <li>最高速度は約 330 km/h、BOOST で 450 km/h 超え。スピードラインと光の軌跡も。</li>
      <li>台湾の高速道路の風景：国道の案内標識、速度制限や速度取締りの標識。</li>
      <li>解除できるボディカラー、10 個の実績、端末内ランキング、スコア画像のシェア。</li>
    </ul>
    <h3>よくある質問</h3>
    <dl>
      <dt>無料ですか？登録は必要？</dt><dd>完全無料で、登録もダウンロードも不要です。</dd>
      <dt>スマホで重いときは？</dt><dd>性能が低い端末では自動で軽量モードになります。右上の HD / SD でも切り替えられます。</dd>
      <dt>テスラ公式のゲームですか？</dt><dd>いいえ。非公式のファンゲームで、Tesla, Inc. とは関係ありません。</dd>
    </dl>
    <p class="more">ハイスコアを狙うなら <a href="ja/guide.html">Roadster Rush 攻略ガイド：スコアの稼ぎ方・危険運転車・ジェット飛行</a> をどうぞ。<br>便利な無料ツールは <a href="https://sectools.tw" target="_blank" rel="noopener">Sectools.tw</a> へ。</p>
''',
}


def seo_block(lang):
    d = SEO[lang]
    url = f'{SITE}/{lang}/'
    faq = ',\n'.join(
        '        ' + json.dumps({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}}, ensure_ascii=False)
        for q, a in d['faq'])
    return f'''<title>{d['title']}</title>
<meta name="description" content="{d['desc']}">
<meta name="keywords" content="{d['keywords']}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="author" content="Sectools.tw">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "VideoGame",
      "name": "{d['name']}",
      "url": "{url}",
      "image": "{SITE}/og.jpg",
      "description": "{d['desc']}",
      "genre": ["Racing", "Arcade", "Endless runner"],
      "gamePlatform": ["Web browser", "Mobile", "Desktop"],
      "applicationCategory": "Game",
      "operatingSystem": "Any",
      "inLanguage": "{d['in_lang']}",
      "isAccessibleForFree": true,
      "datePublished": "2026-10-29",
      "dateModified": "2026-10-29",
      "screenshot": "{SITE}/og.jpg",
      "playMode": "SinglePlayer",
      "offers": {{ "@type": "Offer", "price": "0", "priceCurrency": "{d['currency']}" }},
      "publisher": {{ "@type": "Organization", "name": "Sectools.tw", "url": "https://sectools.tw" }}
    }},
    {{
      "@type": "FAQPage",
      "mainEntity": [
{faq}
      ]
    }}
  ]
}}
</script>
<meta name="theme-color" content="#2a1640">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sectools.tw">
<meta property="og:locale" content="{d['locale']}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{d['og_title']}">
<meta property="og:description" content="{d['og_desc']}">
<meta property="og:image" content="{SITE}/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{d['og_alt']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{d['og_title']}">
<meta name="twitter:description" content="{d['og_desc']}">
<meta name="twitter:image" content="{SITE}/og.jpg">'''


def build(src, lang):
    col = {'en': 1, 'ja': 2}[lang]
    out = src.replace('<html lang="zh-Hant">', f'<html lang="{lang}">', 1)
    # every asset and link in the page is relative to the site root
    out = out.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<base href="../">', 1)
    out = re.sub(r'<!--SEO:START-->.*?<!--SEO:END-->', lambda m: seo_block(lang), out, count=1, flags=re.S)
    out = re.sub(r'<!--ABOUT:START-->.*?<!--ABOUT:END-->', lambda m: ABOUT[lang], out, count=1, flags=re.S)
    for row in sorted(STRINGS, key=lambda r: -len(r[0])):
        zh = row[0]
        assert zh in out, f'[{lang}] source string not found (was it reworded in index.html?): {zh[:70]}'
        out = out.replace(zh, row[col])
    out = out.replace("'https://tesla-roadster.sectools.tw/'", f"'https://tesla-roadster.sectools.tw/{lang}/'")
    if lang == 'ja':
        out = out.replace('family=Russo+One&family=Noto+Sans+TC', 'family=Russo+One&family=Noto+Sans+JP:wght@500;700;900&family=Noto+Sans+TC')
        out = out.replace('"Noto Sans TC","PingFang TC"', '"Noto Sans JP","Hiragino Sans","Noto Sans TC","PingFang TC"')
    return out


def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    for marker in ('<!--SEO:START-->', '<!--SEO:END-->', '<!--ABOUT:START-->', '<!--ABOUT:END-->'):
        assert marker in src, f'missing marker {marker} in index.html'
    for lang in ('en', 'ja'):
        os.makedirs(os.path.join(ROOT, lang), exist_ok=True)
        path = os.path.join(ROOT, lang, 'index.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(build(src, lang))
        print('wrote', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    sys.exit(main())
