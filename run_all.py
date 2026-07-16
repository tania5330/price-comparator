import subprocess
import sys
import os
import time

def run_command(command, cwd=None, label=""):
    """Ejecutar un comando en un proceso separado"""
    print(f"🚀 Iniciando {label}...")
    return subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

def main():
    print("="*60)
    print("🔄 Iniciando todo el stack: FastAPI + Vite + Streamlit")
    print("="*60)

    # Rutas
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Lista de procesos
    processes = []

    try:
        # 1. Iniciar FastAPI (backend)
        processes.append(run_command(
            "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000",
            cwd=project_root,
            label="FastAPI (http://localhost:8000)"
        ))

        # Esperar un poco para que FastAPI arranque
        time.sleep(3)

        # 2. Iniciar Vite (frontend React)
        processes.append(run_command(
            "npm run dev",
            cwd=project_root,
            label="Vite (http://localhost:5173)"
        ))

        # 3. Iniciar Streamlit
        processes.append(run_command(
            "streamlit run streamlit_app.py",
            cwd=project_root,
            label="Streamlit (http://localhost:8501)"
        ))

        print("\n✅ Todos los servicios están corriendo!")
        print("   🌐 FastAPI: http://localhost:8000")
        print("   🌐 Vite: http://localhost:5173")
        print("   🌐 Streamlit: http://localhost:8501")
        print("\n⌨️ Presiona Ctrl+C para detener todos los servicios.\n")

        # Esperar a que se interrumpa
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"⚠️ El proceso {proc} se detuvo inesperadamente.")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo todos los servicios...")
        for proc in processes:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✅ Todos los servicios detenidos exitosamente.")

if __name__ == "__main__":
    main()
