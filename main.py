import os, sys, glob
from ll1_parser import parse

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(ROOT, "tests")

DEFAULT_EXPECT = {
    "ok": True,
    "fail": False,
    "mixed": None,  
}

def leer_caso(path):
    """Devuelve (nombre, codigo, esperado) leyendo directiva si existe."""
    nombre = os.path.relpath(path, TESTS_DIR)
    carpeta = nombre.split(os.sep)[0]
    default = DEFAULT_EXPECT.get(carpeta, None)

    with open(path, "r", encoding="utf-8") as f:
        contenido = f.read()

    esperado = default
    first_line = contenido.splitlines()[0].strip() if contenido.strip() else ""
    if first_line.startswith("//! EXPECT="):
        val = first_line.split("=", 1)[1].strip().upper()
        if val == "OK": esperado = True
        elif val in ("FALLO", "FAIL"): esperado = False

    if esperado is None:
        raise ValueError(f"El caso '{nombre}' no define EXPECT y está en carpeta 'mixed'.")

    return nombre, contenido, esperado

def correr_archivo(path, trazar=False):
    nombre, codigo, esperado = leer_caso(path)
    print(f"\n=== {nombre} ===")
    ok = parse(codigo, trazar=trazar)
    print("Resultado:", "OK" if ok else "FALLO", f"(esperado: {'OK' if esperado else 'FALLO'})")
    return ok == esperado

def recolectar_paths():
    patrones = [
        os.path.join(TESTS_DIR, "ok", "*"),
        os.path.join(TESTS_DIR, "fail", "*"),
        os.path.join(TESTS_DIR, "mixed", "*"),
    ]
    files = []
    for pat in patrones:
        files.extend(glob.glob(pat))
    # Orden estable
    return sorted(f for f in files if os.path.isfile(f))

def main():
    # Uso:
    #  - python main.py                -> corre todos
    #  - python main.py tests/ok/001.c -> corre solo ese (con traza)
    args = sys.argv[1:]
    if args:
        path = args[0]
        ok = correr_archivo(path, trazar=True)
        sys.exit(0 if ok else 1)

    total = 0
    bien = 0
    for path in recolectar_paths():
        total += 1
        try:
            if correr_archivo(path, trazar=False):
                bien += 1
        except Exception as e:
            print(f"[ERROR] {path}: {e}")

    print(f"\nResumen: {bien}/{total} casos en el resultado esperado.")
    sys.exit(0 if bien == total else 1)

if __name__ == "__main__":
    main()


