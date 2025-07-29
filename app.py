from flask import Flask, render_template, request, jsonify
import openai, os, json, sqlite3
from match import filtrar_subsidios
import openai

app = Flask(__name__)


# API Key y modelo
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY no está configurada.")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/subsidios", methods=["POST"])
def subsidios():
    data = request.json
    print("🔍 Datos recibidos:", data)
    matches = filtrar_subsidios(data)

    if not matches:
        return jsonify({"success": False, "error": "No se encontraron programas para tu perfil."})

    context_list = []
    for m in matches:
        context_list.append(
            f"🧾 {m.get('nombre_programa','')}\n"
            f"🏛 {m.get('organismo','Desconocido')}\n"
            f"🧑‍🤝‍🧑 {m.get('grupo_objetivo','')}\n"
            f"📅 Vigencia: {m.get('vigencia','N/D')}\n"
            f"🔗 {m.get('url_oficial','')}"
        )
    context_text = "\n\n".join(context_list)

    system_msg = (
        "Eres un asistente experto en programas sociales argentinos. "
        "Responde únicamente con la información proporcionada en el contexto. "
        "Si falta algún dato, di 'Información no disponible'."
    )

    prompt_msgs = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"Contexto:\n{context_text}\n\nGenera una explicación amable para el usuario."}
    ]

    try:
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt_msgs,
            max_tokens=700
        )
        answer = rsp["choices"][0]["message"]["content"]
        return jsonify({"success": True, "respuesta": answer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/debug")
def debug_data():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM subsidios LIMIT 20")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
