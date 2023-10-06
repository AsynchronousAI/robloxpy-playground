# Copy https://raw.githubusercontent.com/roblox-compilers/roblox-py-dev/main/src/rbxpy.py as rbxpy.py in the cwd

from flask import Flask, render_template_string, jsonify, request
import os
import tempfile
import pylint
import epylint

path = "https://raw.githubusercontent.com/roblox-compilers/roblox-py-dev/main/src/rbxpy.py"
os.system(f"curl {path} > rbxpy.py")
import rbxpy as compile

app = Flask(__name__)

jsCode = """function pythonValidator(value, lintAsync, options, cm) {
    function getXmlHttp(){
        try {
            return new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                return new ActiveXObject("Microsoft.XMLHTTP");
            } catch (ee) {
            }
        }
        if (typeof XMLHttpRequest!='undefined') {
            return new XMLHttpRequest();
        }
    }

    var xmlhttp = getXmlHttp()
    xmlhttp.open("POST", "/lint", true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4) {
            if(xmlhttp.status == 200) {
                var result = [];
                var messages = JSON.parse(xmlhttp.responseText);
                for (var i in messages) {
                    var message = messages[i];
                    var severity = 'warning';
                    if (message.type === 'error' || message.type === 'fatal') {
                        severity = 'error';
                    }

                    result.push({message: message.message,
                                severity:severity,
                                from: CodeMirror.Pos(message.line - 1, message.column),
                                to: CodeMirror.Pos(message.line - 1, message.column)});
                }

                lintAsync(cm, result);
            }
        }
    };

    xmlhttp.send("code=" + encodeURIComponent(value));
}"""
htmlCode = """<!DOCTYPE html>
<html>
<head>
    <title>roblox-py online</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/theme/base16-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/python/python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/addon/lint/lint.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/lua/lua.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/addon/lint/lint.min.css">
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
        """+jsCode+"""
        var pythonEditor = CodeMirror.fromTextArea(document.querySelector(".python"), {
            mode: "python",
            lineNumbers: true,
            theme: "base16-dark",
            indentUnit: 4,
            indentWithTabs: true,
            tabSize: 4,
            autofocus: true,
            //gutters: ["CodeMirror-lint-markers"],
            //lint: {
            //    "getAnnotations": pythonValidator,
            //    "async": true,
            //}
        });
        var luaEditor = CodeMirror.fromTextArea(document.querySelector(".lua"), {
            mode: "lua",
            lineNumbers: true,
            theme: "base16-dark",
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



@app.route('/lint', methods=['POST'])
def lint_action():
    file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    file.write(request.form['code'])
    file.close()

    options = ' '.join([
        file.name,
        '--output-format', 'json',
    ])

    (lint_stdout, lint_stderr) = epylint.py_run(return_std=True, command_options=options)

    os.remove(file.name)
    val = (lint_stdout.read().decode())
    return val

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
