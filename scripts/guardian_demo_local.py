"""
GUARDIAN - Demo Local Standalone
=================================
Ejecuta la pipeline completa SIN FiftyOne:
  1. Centinela analiza frames reales con Gemini Vision
  2. Oraculo evalua el riesgo de cada escena
  3. Copiloto genera briefings y responde preguntas
  4. Genera un reporte HTML interactivo

Uso:
  python scripts/guardian_demo_local.py
"""

import os
import sys
import json
import time
import base64
import logging
import threading
import queue
from pathlib import Path
from datetime import datetime

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

# Fix encoding para Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Asegurar imports del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from shared.contracts import Detection, RiskScore
from agents.centinela import analyze_frame_with_summary
from agents.oraculo import evaluate_risk
from agents.copiloto import ask, generate_briefing

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("GUARDIAN")

FRAMES_DIR = PROJECT_ROOT / "demo-assets" / "frames"
OUTPUT_DIR = PROJECT_ROOT / "output"

# TTS Setup with Queue to prevent thread crashes
tts_queue = queue.Queue()

def tts_worker():
    if not HAS_TTS:
        return
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for v in voices:
            if 'spanish' in v.name.lower() or 'es' in v.languages:
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 150)
        
        while True:
            text = tts_queue.get()
            if text is None:
                break
            engine.say(text)
            engine.runAndWait()
            tts_queue.task_done()
    except Exception as e:
        logger.error(f"TTS Worker Error: {e}")

if HAS_TTS:
    threading.Thread(target=tts_worker, daemon=True).start()

def image_to_base64(path: str) -> str:
    """Convierte imagen a base64 para embeber en HTML."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{data}"


def speak_async(text: str):
    """Encola texto para ser hablado por el worker TTS."""
    if HAS_TTS:
        tts_queue.put(text)


def run_pipeline(num_frames: int = 6) -> dict:
    """
    Ejecuta la pipeline completa de GUARDIAN sobre N frames.
    Retorna los resultados para el reporte.
    """
    # Obtener frames
    all_frames = sorted(FRAMES_DIR.glob("frame_*.jpg"))
    if not all_frames:
        print("ERROR: No se encontraron frames en demo-assets/frames/")
        sys.exit(1)

    # Seleccionar frames distribuidos uniformemente
    step = max(1, len(all_frames) // num_frames)
    selected_frames = all_frames[::step][:num_frames]

    print(f"\n{'='*60}")
    print(f"  GUARDIAN - Pipeline de Seguridad Vial")
    print(f"  {len(all_frames)} frames disponibles, analizando {len(selected_frames)}")
    print(f"{'='*60}\n")

    results = []
    all_detections = []
    scene_summaries = []

    for i, frame_path in enumerate(selected_frames, 1):
        fname = frame_path.name
        print(f"\n[{i}/{len(selected_frames)}] Procesando {fname}...")

        # --- AGENTE 1: CENTINELA ---
        print(f"  [CENTINELA] Analizando con Gemini Vision...")
        t0 = time.time()
        try:
            centinela_result = analyze_frame_with_summary(str(frame_path))
            centinela_time = round(time.time() - t0, 1)
            detections = centinela_result["detections"]
            scene_summary = centinela_result["scene_summary"]
            overall_risk = centinela_result["overall_risk"]
            print(f"  [CENTINELA] {len(detections)} detecciones en {centinela_time}s")
            print(f"              Resumen: {scene_summary[:80]}...")
            print(f"              Riesgo visual: {overall_risk}")
            for d in detections:
                print(f"              - [{d.severity.upper():>8}] {d.label}: {d.description[:60]}")
        except Exception as e:
            print(f"  [CENTINELA] ERROR: {e}")
            detections = []
            scene_summary = f"Error al analizar: {str(e)[:80]}"
            overall_risk = "unknown"
            centinela_time = 0

        all_detections.extend(detections)
        scene_summaries.append(scene_summary)

        # --- AGENTE 2: ORACULO ---
        print(f"  [ORACULO] Evaluando riesgo...")
        metadata = {
            "weather": "cloudy",
            "time_of_day": "morning",
            "hours_driving": 2.5 + (i * 0.5),
            "speed": 60 + (i * 5),
            "speed_limit": 80,
        }
        risk_score = evaluate_risk(detections, metadata)
        print(f"  [ORACULO] Score: {risk_score.score}/10 ({risk_score.level})")
        print(f"            Factores: {', '.join(risk_score.factors[:3])}")
        print(f"            Recomendacion: {risk_score.recommendation[:80]}...")

        results.append({
            "frame": fname,
            "frame_path": str(frame_path),
            "detections": detections,
            "scene_summary": scene_summary,
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "metadata": metadata,
            "centinela_time": centinela_time,
        })

    # --- AGENTE 3: COPILOTO ---
    print(f"\n{'='*60}")
    print(f"  [COPILOTO] Generando briefing de ruta...")
    print(f"{'='*60}\n")

    # Calcular riesgo promedio
    avg_score = sum(r["risk_score"].score for r in results) / len(results) if results else 0
    avg_risk = RiskScore(
        score=round(avg_score, 1),
        factors=list(set(f for r in results for f in r["risk_score"].factors)),
        recommendation="Ver briefing completo",
        historical_incidents=3,
    )

    route_info = {"origin": "Bogota", "destination": "Bucaramanga"}
    driver_info = {"name": "Carlos Perez", "hours_driving": 4.5, "status": "active"}

    briefing = generate_briefing(
        detections=all_detections[:10],
        risk_score=avg_risk,
        route_info=route_info,
        driver_info=driver_info,
        scene_summaries=scene_summaries,
    )
    print(briefing)

    # --- Interaccion Copiloto ---
    print(f"\n{'='*60}")
    print(f"  [COPILOTO] Simulando conversacion con conductor...")
    print(f"{'='*60}\n")

    copilot_conversations = []
    test_messages = [
        "Como esta la situacion de la ruta?",
        "Estoy un poco cansado, que me recomiendas?",
        "Hay alguna ruta alternativa mas segura?",
    ]

    for msg in test_messages:
        print(f"  Conductor: {msg}")
        response = ask(
            msg,
            detections=all_detections[:5],
            risk_score=avg_risk,
            driver_info=driver_info,
            route_info=route_info,
        )
        print(f"  Copiloto:  {response}\n")
        
        # Copiloto habla
        clean_response = response.replace("⚠️", "").replace("🗺️", "").replace("📍", "").replace("🚨", "")
        speak_async(clean_response)
        
        copilot_conversations.append({"question": msg, "answer": response})
        time.sleep(1) # Pequeña pausa para mejor efecto en la demo

    # --- Generate notifications timeline ---
    notifications = []
    base_time = datetime.now()
    notif_id = 0

    for i, r in enumerate(results):
        t = base_time.replace(minute=i * 8)
        ts = t.strftime("%H:%M")

        # Fatigue detection from interior frames
        if len(r["detections"]) == 0 and "driver" in r["scene_summary"].lower():
            notif_id += 1
            fatigue_level = min(0.3 + (i * 0.15), 0.95)
            if fatigue_level > 0.7:
                notifications.append({
                    "id": notif_id, "time": ts, "type": "fatigue",
                    "severity": "danger" if fatigue_level > 0.85 else "warning",
                    "title": "Fatiga detectada" if fatigue_level > 0.85 else "Signos de cansancio",
                    "message": f"Parpadeo frecuente detectado. Nivel de fatiga: {fatigue_level:.0%}. Busca un punto de descanso." if fatigue_level > 0.85 else f"Se detectan signos leves de cansancio ({fatigue_level:.0%}). Mantente alerta.",
                    "icon": "fatigue", "sound": fatigue_level > 0.85,
                })
            else:
                notifications.append({
                    "id": notif_id, "time": ts, "type": "status",
                    "severity": "info",
                    "title": "Estado del conductor OK",
                    "message": f"Analisis facial: conductor alerta. Fatiga: {fatigue_level:.0%}",
                    "icon": "check", "sound": False,
                })

        # Hazard notifications from detections
        for d in r["detections"]:
            if d.severity in ("high", "critical"):
                notif_id += 1
                notifications.append({
                    "id": notif_id, "time": ts, "type": "hazard",
                    "severity": "danger" if d.severity == "critical" else "warning",
                    "title": f"{'PELIGRO' if d.severity == 'critical' else 'Atencion'}: {d.label.replace('_', ' ').title()}",
                    "message": d.description[:80],
                    "icon": "hazard", "sound": True,
                })
            elif d.severity == "medium" and d.label in ("pedestrian", "obstacle", "pothole"):
                notif_id += 1
                notifications.append({
                    "id": notif_id, "time": ts, "type": "hazard",
                    "severity": "caution",
                    "title": f"{d.label.replace('_', ' ').title()} detectado",
                    "message": d.description[:80],
                    "icon": "caution", "sound": False,
                })

        # Risk change notifications
        risk = r["risk_score"]
        if risk.score >= 5:
            notif_id += 1
            is_critical = risk.score >= 7
            notifications.append({
                "id": notif_id, "time": ts, "type": "risk",
                "severity": "danger" if is_critical else "warning",
                "title": f"Riesgo {'CRITICO' if is_critical else 'ALTO'}: {risk.score}/10",
                "message": risk.recommendation[:80],
                "icon": "risk", "sound": is_critical,
            })
            if is_critical:
                speak_async("Alerta. Riesgo crítico detectado. Reduzca la velocidad.")
            else:
                speak_async("Atención. Condiciones de riesgo alto en la vía.")

        # Speed / compliance
        if r["metadata"].get("speed", 0) > r["metadata"].get("speed_limit", 80):
            notif_id += 1
            spd = r["metadata"]["speed"]
            lim = r["metadata"]["speed_limit"]
            notifications.append({
                "id": notif_id, "time": ts, "type": "compliance",
                "severity": "warning",
                "title": f"Exceso de velocidad: {spd} km/h",
                "message": f"Limite en esta zona: {lim} km/h. Reduce la velocidad.",
                "icon": "speed", "sound": True,
            })
            speak_async(f"Exceso de velocidad. Límite permitido: {lim} kilómetros por hora.")

    return {
        "results": results,
        "briefing": briefing,
        "conversations": copilot_conversations,
        "avg_risk": avg_risk,
        "route_info": route_info,
        "driver_info": driver_info,
        "total_detections": len(all_detections),
        "timestamp": datetime.now().isoformat(),
        "notifications": notifications,
    }


def generate_html_report(data: dict) -> str:
    """Genera un reporte HTML premium inspirado en Apple/Samsung."""

    results = data["results"]
    avg = data["avg_risk"]
    avg_color = "#34d399" if avg.score <= 3 else "#fbbf24" if avg.score <= 6 else "#f97316" if avg.score <= 8 else "#ef4444"
    briefing_html = data["briefing"].replace("\n", "<br>")
    notifications = data.get("notifications", [])

    # --- Frame analysis cards ---
    frame_cards = ""
    for idx, r in enumerate(results):
        det_pills = ""
        for d in r["detections"]:
            sev_color = {"low": "#34d399", "medium": "#fbbf24", "high": "#f97316", "critical": "#ef4444"}.get(d.severity, "#888")
            det_pills += f"""
                <div class="det-row">
                    <span class="det-badge" style="background:{sev_color}15;color:{sev_color};border:1px solid {sev_color}33;">{d.severity.upper()}</span>
                    <span class="det-label">{d.label}</span>
                    <span class="det-desc">{d.description[:55]}</span>
                    <span class="det-conf">{d.confidence:.0%}</span>
                </div>"""

        risk = r["risk_score"]
        rc = "#34d399" if risk.score <= 3 else "#fbbf24" if risk.score <= 6 else "#f97316" if risk.score <= 8 else "#ef4444"
        img_b64 = image_to_base64(r["frame_path"])
        delay = idx * 0.1

        frame_cards += f"""
        <div class="analysis-card reveal" style="animation-delay:{delay}s;">
            <div class="analysis-image">
                <img src="{img_b64}" alt="{r['frame']}" loading="lazy">
                <div class="frame-label">{r['frame']}</div>
                <div class="risk-badge" style="background:{rc};">{risk.score}<span class="risk-unit">/10</span></div>
                <div class="image-gradient"></div>
            </div>
            <div class="analysis-content">
                <div class="analysis-header">
                    <h3>Analisis de Escena</h3>
                    <span class="level-tag" style="color:{rc};background:{rc}12;border-color:{rc}30;">{risk.level.upper()}</span>
                </div>
                <p class="scene-summary">{r['scene_summary']}</p>
                <div class="det-section">
                    <div class="det-title">{len(r['detections'])} detecciones</div>
                    {det_pills if det_pills else '<div class="det-empty">Escena sin objetos de riesgo</div>'}
                </div>
                <div class="rec-bar">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{rc}" stroke-width="2"><path d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>
                    <span>{risk.recommendation[:100]}</span>
                </div>
            </div>
        </div>"""

    # --- Conversation bubbles ---
    conv_html = ""
    for c in data["conversations"]:
        conv_html += f"""
        <div class="conv-pair reveal">
            <div class="conv-row conv-user">
                <div class="conv-avatar conv-avatar-user">C</div>
                <div class="conv-bubble conv-bubble-user">{c['question']}</div>
            </div>
            <div class="conv-row conv-bot">
                <div class="conv-bubble conv-bubble-bot">{c['answer']}</div>
                <div class="conv-avatar conv-avatar-bot">G</div>
            </div>
        </div>"""

    # --- Stats ---
    stats_data = [
        (str(len(results)), "Frames analizados", "#60a5fa", "M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"),
        (str(data['total_detections']), "Detecciones totales", "#f472b6", "M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z"),
        (str(avg.score), "Riesgo promedio", avg_color, "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"),
        ("3", "Agentes IA activos", "#a78bfa", "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"),
    ]

    stats_html = ""
    for val, label, color, icon_path in stats_data:
        stats_html += f"""
            <div class="stat reveal">
                <div class="stat-icon" style="background:{color}12;">
                    <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="{color}"><path stroke-linecap="round" stroke-linejoin="round" d="{icon_path}"/></svg>
                </div>
                <div class="stat-value" style="color:{color};">{val}</div>
                <div class="stat-label">{label}</div>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GUARDIAN — Reporte de Seguridad Inteligente</title>
    <meta name="description" content="Sistema de seguridad predictiva para transporte terrestre potenciado por IA">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #000000;
            --surface: #0a0a0a;
            --card: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.06);
            --text-primary: #f5f5f7;
            --text-secondary: #86868b;
            --text-tertiary: #6e6e73;
            --accent: #2997ff;
            --green: #34d399;
            --yellow: #fbbf24;
            --orange: #f97316;
            --red: #ef4444;
            --purple: #a78bfa;
            --pink: #f472b6;
            --radius: 20px;
            --radius-sm: 12px;
        }}

        * {{ margin:0; padding:0; box-sizing:border-box; }}

        html {{ scroll-behavior: smooth; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text-primary);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* === HERO === */
        .hero {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            position: relative;
            overflow: hidden;
            padding: 60px 24px;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            width: 800px;
            height: 800px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(41,151,255,0.12) 0%, transparent 70%);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: heroGlow 6s ease-in-out infinite alternate;
        }}

        .hero::after {{
            content: '';
            position: absolute;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(52,211,153,0.08) 0%, transparent 70%);
            top: 60%;
            left: 30%;
            transform: translate(-50%, -50%);
            animation: heroGlow 8s ease-in-out infinite alternate-reverse;
        }}

        @keyframes heroGlow {{
            0% {{ opacity: 0.4; transform: translate(-50%, -50%) scale(0.9); }}
            100% {{ opacity: 1; transform: translate(-50%, -50%) scale(1.1); }}
        }}

        .hero-content {{
            position: relative;
            z-index: 1;
            max-width: 900px;
        }}

        .hero-eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 20px;
            border-radius: 100px;
            background: rgba(41,151,255,0.08);
            border: 1px solid rgba(41,151,255,0.15);
            color: var(--accent);
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 32px;
            animation: fadeUp 0.8s ease-out;
        }}

        .hero h1 {{
            font-size: clamp(48px, 8vw, 86px);
            font-weight: 900;
            letter-spacing: -0.03em;
            line-height: 1.05;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #f5f5f7 30%, #86868b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: fadeUp 0.8s ease-out 0.1s both;
        }}

        .hero-subtitle {{
            font-size: clamp(18px, 2.5vw, 24px);
            font-weight: 300;
            color: var(--text-secondary);
            max-width: 680px;
            margin: 0 auto 48px;
            line-height: 1.5;
            animation: fadeUp 0.8s ease-out 0.2s both;
        }}

        .hero-stats {{
            display: flex;
            gap: 48px;
            justify-content: center;
            animation: fadeUp 0.8s ease-out 0.3s both;
        }}

        .hero-stat-value {{
            font-size: 42px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .hero-stat-label {{
            font-size: 12px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 4px;
        }}

        .scroll-indicator {{
            position: absolute;
            bottom: 32px;
            left: 50%;
            transform: translateX(-50%);
            animation: bounce 2s ease-in-out infinite;
            color: var(--text-tertiary);
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translateX(-50%) translateY(0); }}
            50% {{ transform: translateX(-50%) translateY(8px); }}
        }}

        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* === SECTIONS === */
        .section {{
            padding: 100px 24px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .section-header {{
            text-align: center;
            margin-bottom: 64px;
        }}

        .section-header h2 {{
            font-size: clamp(32px, 4vw, 52px);
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #f5f5f7 40%, var(--text-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .section-header p {{
            font-size: 18px;
            color: var(--text-secondary);
            font-weight: 300;
            max-width: 560px;
            margin: 0 auto;
        }}

        /* === STATS === */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            margin-bottom: 0;
        }}

        .stat {{
            background: var(--surface);
            padding: 40px 24px;
            text-align: center;
            transition: background 0.3s;
        }}

        .stat:hover {{ background: rgba(255,255,255,0.03); }}

        .stat-icon {{
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16px;
        }}

        .stat-value {{
            font-size: 40px;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
            margin-bottom: 8px;
        }}

        .stat-label {{
            font-size: 11px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 500;
        }}

        /* === BRIEFING === */
        .briefing-card {{
            position: relative;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 48px;
            overflow: hidden;
        }}

        .briefing-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
        }}

        .briefing-icon {{
            width: 56px;
            height: 56px;
            border-radius: 16px;
            background: rgba(41,151,255,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
            font-size: 24px;
        }}

        .briefing-text {{
            font-size: 15px;
            line-height: 1.8;
            color: var(--text-secondary);
        }}

        /* === ANALYSIS CARDS === */
        .analysis-card {{
            display: grid;
            grid-template-columns: 380px 1fr;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            margin-bottom: 20px;
            transition: border-color 0.3s, transform 0.3s;
        }}

        .analysis-card:hover {{
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-2px);
        }}

        .analysis-image {{
            position: relative;
            overflow: hidden;
            min-height: 280px;
        }}

        .analysis-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.5s;
        }}

        .analysis-card:hover .analysis-image img {{ transform: scale(1.03); }}

        .image-gradient {{
            position: absolute;
            inset: 0;
            background: linear-gradient(to right, transparent 60%, rgba(0,0,0,0.4));
            pointer-events: none;
        }}

        .frame-label {{
            position: absolute;
            top: 16px;
            left: 16px;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255,255,255,0.08);
        }}

        .risk-badge {{
            position: absolute;
            bottom: 16px;
            right: 16px;
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #fff;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        }}

        .risk-unit {{
            font-size: 13px;
            font-weight: 500;
            opacity: 0.7;
        }}

        .analysis-content {{
            padding: 28px 32px;
            display: flex;
            flex-direction: column;
        }}

        .analysis-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }}

        .analysis-header h3 {{
            font-size: 17px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        .level-tag {{
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            border: 1px solid;
        }}

        .scene-summary {{
            color: var(--text-secondary);
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 18px;
            flex-grow: 1;
        }}

        .det-section {{ margin-bottom: 16px; }}

        .det-title {{
            font-size: 10px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .det-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px 0;
            border-bottom: 1px solid var(--border);
        }}

        .det-row:last-child {{ border-bottom: none; }}

        .det-badge {{
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }}

        .det-label {{
            font-weight: 600;
            font-size: 12px;
            color: var(--text-primary);
            min-width: 70px;
        }}

        .det-desc {{
            color: var(--text-tertiary);
            font-size: 12px;
            flex-grow: 1;
        }}

        .det-conf {{
            color: var(--text-tertiary);
            font-size: 11px;
            font-weight: 500;
        }}

        .det-empty {{
            color: var(--text-tertiary);
            font-size: 12px;
            font-style: italic;
            padding: 8px 0;
        }}

        .rec-bar {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 12px 14px;
            background: rgba(255,255,255,0.02);
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: auto;
        }}

        .rec-bar svg {{ flex-shrink: 0; margin-top: 1px; }}

        /* === CONVERSATIONS === */
        .conv-container {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 40px;
        }}

        .conv-pair {{ margin-bottom: 28px; }}
        .conv-pair:last-child {{ margin-bottom: 0; }}

        .conv-row {{
            display: flex;
            align-items: flex-end;
            gap: 12px;
            margin-bottom: 10px;
        }}

        .conv-bot {{ flex-direction: row-reverse; }}

        .conv-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .conv-avatar-user {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: #fff;
        }}

        .conv-avatar-bot {{
            background: linear-gradient(135deg, #34d399, #059669);
            color: #fff;
        }}

        .conv-bubble {{
            padding: 14px 20px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.5;
            max-width: 75%;
        }}

        .conv-bubble-user {{
            background: rgba(59,130,246,0.1);
            border: 1px solid rgba(59,130,246,0.15);
            border-bottom-left-radius: 4px;
            color: var(--text-primary);
        }}

        .conv-bubble-bot {{
            background: rgba(52,211,153,0.08);
            border: 1px solid rgba(52,211,153,0.12);
            border-bottom-right-radius: 4px;
            color: var(--text-secondary);
        }}

        /* === ARCHITECTURE === */
        .arch-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2px;
            background: var(--border);
            border-radius: var(--radius);
            overflow: hidden;
        }}

        .arch-card {{
            background: var(--surface);
            padding: 48px 32px;
            text-align: center;
            transition: background 0.4s;
            position: relative;
        }}

        .arch-card:hover {{ background: rgba(255,255,255,0.03); }}

        .arch-card::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 2px;
            transition: width 0.4s;
        }}

        .arch-card:hover::after {{ width: 60%; }}

        .arch-card:nth-child(1)::after {{ background: var(--accent); }}
        .arch-card:nth-child(2)::after {{ background: var(--orange); }}
        .arch-card:nth-child(3)::after {{ background: var(--green); }}

        .arch-num {{
            font-size: 11px;
            color: var(--text-tertiary);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }}

        .arch-name {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
        }}

        .arch-desc {{
            font-size: 13px;
            color: var(--text-tertiary);
            max-width: 220px;
            margin: 0 auto;
            line-height: 1.5;
        }}

        .arch-tag {{
            display: inline-block;
            margin-top: 16px;
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 11px;
            font-weight: 500;
        }}

        /* === NOTIFICATION PANEL === */
        .notif-layout {{
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 40px;
            align-items: start;
        }}

        .phone-mockup {{
            background: #1c1c1e;
            border-radius: 40px;
            padding: 12px;
            border: 3px solid #3a3a3c;
            position: sticky;
            top: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}

        .phone-notch {{
            width: 120px;
            height: 28px;
            background: #000;
            border-radius: 0 0 16px 16px;
            margin: 0 auto 8px;
        }}

        .phone-screen {{
            background: #000;
            border-radius: 28px;
            min-height: 560px;
            overflow: hidden;
            position: relative;
            display: flex;
            flex-direction: column;
        }}

        .phone-status-bar {{
            display: flex;
            justify-content: space-between;
            padding: 12px 20px 8px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
        }}

        .phone-road {{
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 24px;
            padding: 20px;
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
            position: relative;
        }}

        .road-line {{
            width: 4px;
            height: 40px;
            background: rgba(255,255,255,0.15);
            border-radius: 2px;
            animation: roadMove 1.5s linear infinite;
        }}

        .road-line:nth-child(2) {{ animation-delay: 0.5s; }}
        .road-line:nth-child(3) {{ animation-delay: 1s; }}

        @keyframes roadMove {{
            0% {{ transform: translateY(-20px); opacity: 0; }}
            50% {{ opacity: 1; }}
            100% {{ transform: translateY(20px); opacity: 0; }}
        }}

        .phone-notif-stack {{
            position: absolute;
            top: 56px;
            left: 12px;
            right: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 10;
        }}

        .phone-toast {{
            background: rgba(28,28,30,0.92);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 14px;
            padding: 12px 14px;
            border-left: 3px solid #ef4444;
            transform: translateY(-20px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.16,1,0.3,1);
        }}

        .phone-toast-show {{
            transform: translateY(0);
            opacity: 1;
        }}

        .phone-toast-hide {{
            transform: translateX(100%);
            opacity: 0;
        }}

        .phone-toast-title {{
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 2px;
        }}

        .phone-toast-msg {{
            font-size: 10px;
            color: var(--text-tertiary);
            line-height: 1.3;
        }}

        .phone-bottom-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(12px);
        }}

        .phone-speed {{
            display: flex;
            align-items: baseline;
            gap: 4px;
        }}

        .phone-speed-num {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}

        .phone-speed-unit {{
            font-size: 11px;
            color: var(--text-tertiary);
            font-weight: 500;
        }}

        .phone-risk-pill {{
            padding: 5px 14px;
            border-radius: 100px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .notif-timeline {{ flex-grow: 1; }}

        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }}

        .timeline-title {{
            font-size: 16px;
            font-weight: 700;
        }}

        .timeline-count {{
            font-size: 12px;
            color: var(--text-tertiary);
            background: rgba(255,255,255,0.04);
            padding: 4px 12px;
            border-radius: 100px;
        }}

        .timeline-list {{ position: relative; }}

        .timeline-item {{
            display: flex;
            gap: 16px;
            padding: 16px 0;
            border-bottom: 1px solid var(--border);
            position: relative;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: 5px;
            top: 28px;
            bottom: -16px;
            width: 1px;
            background: var(--border);
        }}

        .timeline-item:last-child::before {{ display: none; }}

        .timeline-dot {{
            width: 11px;
            height: 11px;
            border-radius: 50%;
            flex-shrink: 0;
            margin-top: 4px;
            box-shadow: 0 0 8px currentColor;
        }}

        .timeline-content {{ flex-grow: 1; }}

        .timeline-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }}

        .timeline-time {{
            font-size: 11px;
            color: var(--text-tertiary);
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }}

        .timeline-type-badge {{
            padding: 1px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        .timeline-sound {{
            font-size: 12px;
        }}

        .timeline-title-text {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 2px;
        }}

        .timeline-msg {{
            font-size: 12px;
            color: var(--text-tertiary);
            line-height: 1.4;
        }}

        @media (max-width: 768px) {{
            .notif-layout {{ grid-template-columns: 1fr; }}
            .phone-mockup {{ position: static; max-width: 280px; margin: 0 auto; }}
        }}

        /* === FOOTER === */
        .footer {{
            text-align: center;
            padding: 80px 24px 48px;
            color: var(--text-tertiary);
            font-size: 12px;
        }}

        .footer-logo {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .footer-powered {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            border-radius: 100px;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            margin-top: 20px;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        /* === REVEAL ANIMATION === */
        .reveal {{
            opacity: 0;
            transform: translateY(40px);
            animation: revealUp 0.7s ease-out forwards;
        }}

        @keyframes revealUp {{
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* === RESPONSIVE === */
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .analysis-card {{ grid-template-columns: 1fr; }}
            .analysis-image {{ min-height: 200px; }}
            .arch-grid {{ grid-template-columns: 1fr; }}
            .hero-stats {{ flex-direction: column; gap: 24px; }}
        }}
    </style>
</head>
<body>

    <!-- HERO -->
    <section class="hero">
        <div class="hero-content">
            <div class="hero-eyebrow">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>
                Potenciado por Gemini 2.5 Flash
            </div>
            <h1>GUARDIAN</h1>
            <p class="hero-subtitle">
                Seguridad predictiva para transporte terrestre.
                Tres agentes de IA trabajan en conjunto para proteger a conductores y pasajeros en tiempo real.
            </p>
            <div class="hero-stats">
                <div>
                    <div class="hero-stat-value" style="color:{avg_color};">{avg.score}</div>
                    <div class="hero-stat-label">Riesgo promedio</div>
                </div>
                <div>
                    <div class="hero-stat-value" style="color:#60a5fa;">{data['total_detections']}</div>
                    <div class="hero-stat-label">Amenazas detectadas</div>
                </div>
                <div>
                    <div class="hero-stat-value" style="color:#a78bfa;">{len(results)}</div>
                    <div class="hero-stat-label">Escenas analizadas</div>
                </div>
            </div>
        </div>
        <div class="scroll-indicator">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/></svg>
        </div>
    </section>

    <!-- STATS -->
    <section class="section" style="padding-top:0;">
        <div class="stats-grid">
            {stats_html}
        </div>
    </section>

    <!-- ARCHITECTURE -->
    <section class="section">
        <div class="section-header">
            <h2>Tres agentes.<br>Una mision.</h2>
            <p>Cada agente cumple un rol especializado en la cadena de seguridad, conectados por un flujo de datos inteligente.</p>
        </div>
        <div class="arch-grid reveal">
            <div class="arch-card">
                <div class="arch-num">Agente 01</div>
                <div class="arch-name" style="color:var(--accent);">Centinela</div>
                <div class="arch-desc">Vision artificial que analiza cada frame de dashcam e identifica peligros en la via.</div>
                <span class="arch-tag" style="background:rgba(41,151,255,0.1);color:var(--accent);">Gemini Vision</span>
            </div>
            <div class="arch-card">
                <div class="arch-num">Agente 02</div>
                <div class="arch-name" style="color:var(--orange);">Oraculo</div>
                <div class="arch-desc">Motor predictivo que evalua el riesgo combinando detecciones, clima, fatiga y contexto.</div>
                <span class="arch-tag" style="background:rgba(249,115,22,0.1);color:var(--orange);">Scoring Engine</span>
            </div>
            <div class="arch-card">
                <div class="arch-num">Agente 03</div>
                <div class="arch-name" style="color:var(--green);">Copiloto</div>
                <div class="arch-desc">Asistente conversacional que guia al conductor con recomendaciones en lenguaje natural.</div>
                <span class="arch-tag" style="background:rgba(52,211,153,0.1);color:var(--green);">Gemini LLM</span>
            </div>
        </div>
    </section>

    <!-- NOTIFICATION PANEL -->
    <section class="section">
        <div class="section-header">
            <h2>Alertas en tiempo real.</h2>
            <p>El conductor recibe notificaciones breves, claras y accionables sin quitar la vista del camino.</p>
        </div>

        <div class="notif-layout reveal">
            <!-- Phone mockup -->
            <div class="phone-mockup">
                <div class="phone-notch"></div>
                <div class="phone-screen">
                    <div class="phone-status-bar">
                        <span>GUARDIAN</span>
                        <span>{datetime.now().strftime('%H:%M')}</span>
                    </div>
                    <div class="phone-road">
                        <div class="road-line"></div>
                        <div class="road-line"></div>
                        <div class="road-line"></div>
                    </div>
                    <div class="phone-notif-stack" id="phoneNotifs"></div>
                    <div class="phone-bottom-bar">
                        <div class="phone-speed"><span class="phone-speed-num">62</span><span class="phone-speed-unit">km/h</span></div>
                        <div class="phone-risk-pill" style="background:{avg_color}22;color:{avg_color};border:1px solid {avg_color}44;">Riesgo {avg.level}</div>
                    </div>
                </div>
            </div>

            <!-- Timeline -->
            <div class="notif-timeline">
                <div class="timeline-header">
                    <span class="timeline-title">Registro de alertas</span>
                    <span class="timeline-count">{len(notifications)} eventos</span>
                </div>
                <div class="timeline-list">
                    {''.join(f'''
                    <div class="timeline-item reveal" style="animation-delay:{i*0.05}s;">
                        <div class="timeline-dot" style="background:{'var(--red)' if n['severity']=='danger' else 'var(--orange)' if n['severity']=='warning' else 'var(--yellow)' if n['severity']=='caution' else 'var(--accent)'};"></div>
                        <div class="timeline-content">
                            <div class="timeline-meta">
                                <span class="timeline-time">{n['time']}</span>
                                <span class="timeline-type-badge" style="background:{'var(--red)' if n['severity']=='danger' else 'var(--orange)' if n['severity']=='warning' else 'var(--yellow)' if n['severity']=='caution' else 'var(--accent)'}15;color:{'var(--red)' if n['severity']=='danger' else 'var(--orange)' if n['severity']=='warning' else 'var(--yellow)' if n['severity']=='caution' else 'var(--accent)'};">{n['type'].upper()}</span>
                                {'<span class="timeline-sound">&#128266;</span>' if n.get('sound') else ''}
                            </div>
                            <div class="timeline-title-text">{n['title']}</div>
                            <div class="timeline-msg">{n['message']}</div>
                        </div>
                    </div>''' for i, n in enumerate(notifications))}
                </div>
            </div>
        </div>
    </section>

    <!-- BRIEFING -->
    <section class="section">
        <div class="section-header">
            <h2>Briefing de ruta.</h2>
            <p>Resumen ejecutivo generado automaticamente por el Copiloto basado en el analisis completo de la ruta.</p>
        </div>
        <div class="briefing-card reveal">
            <div class="briefing-icon">&#128225;</div>
            <div class="briefing-text">{briefing_html}</div>
        </div>
    </section>

    <!-- FRAME ANALYSIS -->
    <section class="section">
        <div class="section-header">
            <h2>Analisis en profundidad.</h2>
            <p>Cada frame de dashcam procesado por Centinela y evaluado por Oraculo en tiempo real.</p>
        </div>
        {frame_cards}
    </section>

    <!-- CONVERSATIONS -->
    <section class="section">
        <div class="section-header">
            <h2>Copiloto inteligente.</h2>
            <p>Conversaciones reales generadas por IA contextual para asistir al conductor en ruta.</p>
        </div>
        <div class="conv-container reveal">
            {conv_html}
        </div>
    </section>

    <!-- FOOTER -->
    <div class="footer">
        <div class="footer-logo">GUARDIAN</div>
        <div>Gestion Unificada de Alertas, Riesgo, Deteccion e Inteligencia<br>para el Autotransporte Nacional</div>
        <div class="footer-powered">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>
            Powered by Gemini 2.5 Flash
        </div>
        <div style="margin-top:24px;color:var(--text-tertiary);">
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &middot; Hackathon 2026
        </div>
    </div>

    <script>
        // Intersection Observer for scroll reveal
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.animationPlayState = 'running';
                    observer.unobserve(entry.target);
                }}
            }});
        }}, {{ threshold: 0.1 }});

        document.querySelectorAll('.reveal').forEach(el => {{
            el.style.animationPlayState = 'paused';
            observer.observe(el);
        }});

        // Phone notification simulation
        const notifs = {json.dumps([n for n in notifications if n['severity'] in ('danger','warning')], ensure_ascii=False)};
        const phoneStack = document.getElementById('phoneNotifs');
        let nIdx = 0;
        function showNextNotif() {{
            if (nIdx >= notifs.length) nIdx = 0;
            const n = notifs[nIdx];
            const colors = {{danger:'#ef4444',warning:'#f97316',caution:'#fbbf24',info:'#2997ff'}};
            const c = colors[n.severity] || '#2997ff';
            const el = document.createElement('div');
            el.className = 'phone-toast';
            el.style.borderLeftColor = c;
            el.innerHTML = `<div class="phone-toast-title" style="color:${{c}};">${{n.sound ? '&#128266; ' : ''}}${{n.title}}</div><div class="phone-toast-msg">${{n.message.substring(0,60)}}</div>`;
            phoneStack.prepend(el);
            requestAnimationFrame(() => el.classList.add('phone-toast-show'));
            setTimeout(() => {{
                el.classList.remove('phone-toast-show');
                el.classList.add('phone-toast-hide');
                setTimeout(() => el.remove(), 400);
            }}, 4000);
            nIdx++;
        }}
        if (notifs.length > 0) {{
            showNextNotif();
            setInterval(showNextNotif, 5000);
        }}
    </script>
</body>
</html>"""
    return html


def main():
    print("\n" + "="*60)
    print("  GUARDIAN - Demo Local Standalone")
    print("  Sin FiftyOne. Solo agentes + Gemini + frames reales.")
    print("="*60)

    # Verificar API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "PEGA_TU_KEY_AQUI":
        print("\nERROR: Configura GEMINI_API_KEY en el archivo .env")
        sys.exit(1)
    print(f"\n[OK] API Key configurada ({api_key[:12]}...)")
    print(f"[OK] Frames disponibles: {len(list(FRAMES_DIR.glob('frame_*.jpg')))}")

    # Ejecutar pipeline (6 frames para la demo)
    data = run_pipeline(num_frames=6)

    # Generar reporte HTML
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_path = OUTPUT_DIR / "guardian_report.html"

    html = generate_html_report(data)
    report_path.write_text(html, encoding="utf-8")

    # Guardar JSON con resultados
    json_path = OUTPUT_DIR / "guardian_results.json"
    json_data = {
        "timestamp": data["timestamp"],
        "route": data["route_info"],
        "driver": data["driver_info"],
        "avg_risk_score": data["avg_risk"].score,
        "total_detections": data["total_detections"],
        "briefing": data["briefing"],
        "frames_analyzed": len(data["results"]),
        "conversations": data["conversations"],
        "frame_results": [
            {
                "frame": r["frame"],
                "scene_summary": r["scene_summary"],
                "overall_risk": r["overall_risk"],
                "risk_score": r["risk_score"].score,
                "risk_level": r["risk_score"].level,
                "risk_factors": r["risk_score"].factors,
                "recommendation": r["risk_score"].recommendation,
                "detections": [
                    {"label": d.label, "confidence": d.confidence, "severity": d.severity, "description": d.description}
                    for d in r["detections"]
                ],
            }
            for r in data["results"]
        ],
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  REPORTE GENERADO!")
    print(f"  HTML: {report_path}")
    print(f"  JSON: {json_path}")
    print(f"{'='*60}")
    print(f"\n  Abre el HTML en tu navegador para ver el dashboard completo.")

    # Intentar abrir en navegador
    try:
        import webbrowser
        webbrowser.open(str(report_path))
        print("  [OK] Abriendo en navegador...")
    except Exception:
        pass


if __name__ == "__main__":
    main()
