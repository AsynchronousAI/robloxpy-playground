# Copy https://raw.githubusercontent.com/roblox-compilers/roblox-py-dev/main/src/rbxpy.py as rbxpy.py in the cwd

from flask import Flask, render_template_string, request
import subprocess, os
path = "https://raw.githubusercontent.com/roblox-compilers/roblox-py-dev/main/src/rbxpy.py"
os.system(f"curl {path} > rbxpy.py")
import rbxpy as compile

app = Flask(__name__)

htmlCode = """<!DOCTYPE html>
<html>
<head>
    <title>roblox-py online</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/theme/darcula.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/python/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/lua/lua.min.js"></script>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
        }
        .CodeMirror {
            height: 100%;
        }
        .editor-container {
            display: flex;
            height: 100%;
        }
        .editor {
            flex: 1;
            height: 100%;
        }
    </style>
</head>
<body>
    <div class="editor-container">
        <div class="editor">
            <textarea class="codemirror python" name="python"></textarea>
        </div>
        <div class="editor">
            <textarea class="codemirror lua" name="lua" readonly></textarea>
        </div>
    </div>
    <script>
        var pythonEditor = CodeMirror.fromTextArea(document.querySelector(".python"), {
            mode: "python",
            lineNumbers: true,
            theme: "darcula",
            indentUnit: 4,
            indentWithTabs: true,
            tabSize: 4,
            autofocus: true
        });
        var luaEditor = CodeMirror.fromTextArea(document.querySelector(".lua"), {
            mode: "lua",
            lineNumbers: true,
            theme: "darcula",
            indentUnit: 4,
            indentWithTabs: true,
            tabSize: 4,
            readOnly: true
        });
        pythonEditor.on("change", function() {
            var pythonCode = pythonEditor.getValue();
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/");
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var luaCode = xhr.responseText;
                    luaEditor.setValue(luaCode);
                }else{
                  var luaCode = "-- Syntax Error"
                }
            };
            xhr.send("python=" + encodeURIComponent(pythonCode));
        });
    </script>
</body>
</html>"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pythonCode = request.form["python"]
        translator = compile.Translator()
        compile.dependencies = []
        try:
          luaCode = translator.translate(pythonCode, False, isAPI=True)
        except SyntaxError as e:
          luaCode = "-- syntax error: "+str(e)
        except Exception as e:
          luaCode = "-- bug: "+str(e)+"\n-- please report to the RCC Discord Server"
        return render_template_string(luaCode)
    else:
        return render_template_string(htmlCode)

if __name__ == "__main__":
  from waitress import serve
  serve(app, host="0.0.0.0", port=8080)
