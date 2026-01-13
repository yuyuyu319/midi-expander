import os
import io
import time
import mido
from flask import Flask, request, send_file, make_response

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIDI Expander | ダイナミクス強調ツール</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4758959657594096" crossorigin="anonymous"></script>
    <style>
        :root { --accent: #ff5252; --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; text-align: center; padding: 50px 20px; margin:0; line-height: 1.6; }
        .card { background: var(--card); padding: 40px; border-radius: 24px; max-width: 600px; margin: auto; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3); }
        h1 { color: var(--accent); font-size: 2.5rem; margin-bottom: 10px; font-weight: 800; }
        .subtitle { color: #94a3b8; margin-bottom: 30px; font-size: 1.1rem; }
        .form-group { margin: 20px 0; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto; }
        label { display: block; font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        input[type="number"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }
        button { background: var(--accent); color: white; border: none; padding: 18px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; margin-top: 20px; transition: 0.2s; }
        button:hover { transform: translateY(-2px); opacity: 0.9; }
        
        .link-box { margin-top: 25px; padding-top: 20px; border-top: 1px solid #334155; font-size: 0.8rem; color: #94a3b8; }
        .link-box a { text-decoration: none; font-weight: bold; margin: 0 3px; }
        .link-box a.humanizer { color: #00e676; }
        .link-box a.normalizer { color: #00b0ff; }
        .link-box a.limiter { color: #ff9100; }
        .link-box a.compressor { color: #d500f9; }

        .content-section { max-width: 700px; margin: 60px auto; text-align: left; background: rgba(30, 41, 59, 0.5); padding: 40px; border-radius: 20px; border: 1px solid #1e293b; }
        .content-section h2 { color: var(--accent); border-bottom: 2px solid #334155; padding-bottom: 10px; margin-top: 40px; }
        .footer-copy { margin-top: 40px; font-size: 0.75rem; color: #475569; padding-bottom: 40px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>MIDI Expander</h1>
        <p class="subtitle">小さい音をさらに下げ、メリハリを出す。</p>
        <form action="/process" method="post" enctype="multipart/form-data">
            <div style="margin-bottom: 25px; border: 2px dashed #334155; padding: 20px; border-radius: 12px;">
                <input type="file" name="midi_file" accept=".mid,.midi" required style="color: #94a3b8;">
            </div>
            <div class="form-group">
                <label>スレッショルド (1-127)<br><small>※この値以下の音を拡張（減衰）させます</small></label>
                <input type="number" name="threshold" value="60" min="1" max="127">
            </div>
            <div class="form-group">
                <label>レシオ (比率 1.0-10.0)<br><small>※拡張の強さを指定します</small></label>
                <input type="number" name="ratio" value="1.5" step="0.1" min="1.0" max="10.0">
            </div>
            <button type="submit">EXPAND & DOWNLOAD</button>
        </form>
        <div class="link-box">
            関連ツール: 
            <a href="https://midi-humanizer.onrender.com/" class="humanizer">Humanizer</a> | 
            <a href="https://midi-normalizer.onrender.com/" class="normalizer">Normalizer</a> | 
            <a href="https://midi-limiter.onrender.com/" class="limiter">Limiter</a> | 
            <a href="https://midi-compressor.onrender.com/" class="compressor">Compressor</a>
        </div>
    </div>
    <div class="content-section">
        <h2>MIDIエキスパンダーの活用</h2>
        <p>スレッショルド値を下回る微細な音をさらに減衰させることで、アクセントの付いた音とそうでない音の差を広げます。リズムのキレを良くしたり、不要なゴーストノートを目立たなくさせるのに有効です。</p>
    </div>
    <div class="footer-copy">&copy; 2026 MIDI Expander. All rights reserved.</div>
</body>
</html>
"""

def process_logic(midi_file_stream, threshold, ratio):
    midi_file_stream.seek(0); input_data = io.BytesIO(midi_file_stream.read())
    try: mid = mido.MidiFile(file=input_data)
    except: return None
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.velocity < threshold:
                    msg.velocity = int(threshold - (threshold - msg.velocity) * ratio)
                msg.velocity = max(1, min(127, msg.velocity))
    output = io.BytesIO(); mid.save(file=output); output.seek(0); return output

@app.route('/')
def index(): return make_response(HTML_PAGE)

@app.route('/process', methods=['POST'])
def process():
    file = request.files['midi_file']
    threshold = int(request.form.get('threshold', 60))
    ratio = float(request.form.get('ratio', 1.5))
    processed_midi = process_logic(file, threshold, ratio)
    return send_file(processed_midi, as_attachment=True, download_name="expanded.mid", mimetype='audio/midi')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
