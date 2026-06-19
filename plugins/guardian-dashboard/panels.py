"""
GUARDIAN Dashboard — Panel de FiftyOne (centro de control)
ROL 3 — Implementación completa Hora 1 a Hora 5

Campos que este panel espera encontrar en el dataset (coordinar con Rol 1 y Rol 2
si los nombres difieren — son el único acoplamiento fuerte de este archivo):
    sample.vehicle_id        -> str
    sample.driver_id         -> str
    sample.risk_score        -> float (0-10)
    sample.severity          -> "low"|"medium"|"high"|"critical" (o info/warning/danger/emergency)
    sample.alert_title       -> str
    sample.description       -> str
    sample.recommendation    -> str
    sample.location          -> {"lat": float, "lon": float}
    sample.detections        -> fo.Detections (label por detección)
    sample.embedding         -> vector (opcional, Hora 5)
"""

import fiftyone.operators as foo
import fiftyone.operators.types as types


SEVERITY_ICON = {
    "low": "🟢", "info": "🟢",
    "medium": "🟡", "warning": "🟡",
    "high": "🟠", "danger": "🟠",
    "critical": "🔴", "emergency": "🔴",
}

SEVERITY_ORDER = {"critical": 0, "emergency": 0, "high": 1, "danger": 1,
                   "medium": 2, "warning": 2, "low": 3, "info": 3}

SEVERITY_COLOR = {
    "low": "#2e7d32", "info": "#2e7d32",
    "medium": "#f9a825", "warning": "#f9a825",
    "high": "#ef6c00", "danger": "#ef6c00",
    "critical": "#c62828", "emergency": "#c62828",
}


class GuardianDashboard(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="guardian_dashboard",
            label="🛡️ GUARDIAN Dashboard",
            icon="shield",
            category="Analyze",
        )

    # ==================================================================
    # LIFECYCLE (Hora 1)
    # ==================================================================
    def on_load(self, ctx):
        ctx.panel.state.title = "GUARDIAN — Centro de Control"
        ctx.panel.state.severity_filter = "all"
        ctx.panel.state.last_briefing = "Sin briefing aún"
        ctx.panel.state.has_dataset = ctx.dataset is not None

    # ==================================================================
    # DATA HELPERS (Hora 2 -> Hora 3: mock con fallback a datos reales)
    # ==================================================================
    def _safe(self, fn, default):
        try:
            return fn()
        except Exception:
            return default

    def _get_fleet_summary(self, ctx):
        dataset = ctx.dataset
        if dataset is None or len(dataset) == 0:
            return {"total_frames": 0, "vehicles": 0, "drivers": 0, "avg_risk": 0.0, "active_alerts": 0}

        total_frames = len(dataset)
        vehicles = self._safe(
            lambda: len([v for v in dataset.distinct("vehicle_id") if v]), 1
        )
        drivers = self._safe(
            lambda: len([d for d in dataset.distinct("driver_id") if d]), 1
        )
        avg_risk = self._safe(lambda: round(dataset.mean("risk_score") or 0.0, 2), 0.0)
        active_alerts = self._safe(
            lambda: len(dataset.match({"risk_score": {"$gt": 7}})), 0
        )

        return {
            "total_frames": total_frames,
            "vehicles": vehicles or 1,
            "drivers": drivers or 1,
            "avg_risk": avg_risk,
            "active_alerts": active_alerts,
        }

    def _get_alerts(self, ctx, limit=8):
        """Hora 3: lee alertas reales, ordenadas por criticidad. Filtra por severidad si está seteado."""
        dataset = ctx.dataset
        severity_filter = getattr(ctx.panel.state, "severity_filter", "all")

        if dataset is None or len(dataset) == 0:
            return [{
                "severity": "danger",
                "title": "Peatón en vía (mock)",
                "description": "Detección de ejemplo mientras llega el dataset real",
                "recommendation": "Reducir velocidad a 30km/h",
                "risk_score": 8.2,
            }]

        def _query():
            view = dataset.match({"risk_score": {"$gt": 4}})
            if severity_filter != "all":
                view = view.match({"severity": severity_filter})
            view = view.sort_by("risk_score", reverse=True).limit(limit)
            out = []
            for sample in view:
                out.append({
                    "severity": getattr(sample, "severity", "warning"),
                    "title": getattr(sample, "alert_title", None) or sample.filepath.split("/")[-1],
                    "description": getattr(sample, "description", "") or "",
                    "recommendation": getattr(sample, "recommendation", "") or "",
                    "risk_score": getattr(sample, "risk_score", 0.0) or 0.0,
                })
            # orden adicional por severidad por si el sort de risk_score empata
            out.sort(key=lambda a: (SEVERITY_ORDER.get(a["severity"], 9), -a["risk_score"]))
            return out

        return self._safe(_query, [])

    def _get_detection_stats(self, ctx):
        dataset = ctx.dataset
        default = {"vehicle": 0, "pedestrian": 0, "obstacle": 0, "sign": 0, "pothole": 0}
        if dataset is None or len(dataset) == 0:
            return default
        counts = self._safe(
            lambda: dataset.count_values("detections.detections.label"), {}
        )
        return counts or default

    def _get_severity_distribution(self, ctx):
        dataset = ctx.dataset
        if dataset is None or len(dataset) == 0:
            return {}
        return self._safe(lambda: dataset.count_values("severity"), {})

    def _get_vehicle_status(self, ctx):
        """Hora 4/5: estado por vehículo para la vista multi-flota."""
        dataset = ctx.dataset
        if dataset is None or len(dataset) == 0:
            return []

        def _query():
            vehicles = [v for v in dataset.distinct("vehicle_id") if v]
            rows = []
            for vid in vehicles[:10]:
                v_view = dataset.match({"vehicle_id": vid})
                avg_risk = round(v_view.mean("risk_score") or 0.0, 2)
                n_alerts = len(v_view.match({"risk_score": {"$gt": 7}}))
                rows.append({"vehicle_id": vid, "avg_risk": avg_risk, "alerts": n_alerts})
            rows.sort(key=lambda r: -r["avg_risk"])
            return rows

        return self._safe(_query, [])

    # ==================================================================
    # ACTIONS (Hora 4)
    # ==================================================================
    def generate_briefing(self, ctx):
        try:
            ctx.trigger(
                "@guardian/guardian-copiloto/generate_briefing",
                params={"vehicle_id": getattr(ctx.panel.state, "selected_vehicle", None)},
            )
            ctx.panel.state.last_briefing = "Generando briefing... (revisa en unos segundos)"
        except Exception as e:
            ctx.panel.state.last_briefing = f"⚠️ No se pudo generar el briefing: {e}"

    def refresh_briefing_result(self, ctx):
        """Si el operator del copiloto escribe el resultado en ctx.dataset o en un campo
        compartido, aquí lo recogemos. Ajustar según contrato real con Rol 2/4."""
        result = self._safe(lambda: ctx.params.get("briefing_text"), None)
        if result:
            ctx.panel.state.last_briefing = result

    def set_severity_filter(self, ctx):
        value = ctx.params.get("value", "all")
        ctx.panel.state.severity_filter = value

    def clear_filter(self, ctx):
        ctx.panel.state.severity_filter = "all"

    # ==================================================================
    # RENDER (Hora 1 a 5 — todo integrado)
    # ==================================================================
    def render(self, ctx):
        panel = types.Object()

        # ---------- Header ----------
        panel.str("title", view=types.Header(divider=True))
        panel.md(
            "subtitle_md",
            default="### Sistema de seguridad predictiva — vista en tiempo real\n---",
        )

        summary = self._get_fleet_summary(ctx)
        alerts = self._get_alerts(ctx)
        det_stats = self._get_detection_stats(ctx)
        sev_dist = self._get_severity_distribution(ctx)
        fleet_status = self._get_vehicle_status(ctx)

        # ============================================================
        # SECCIÓN 1 — Resumen de Flota (Hora 2/3)
        # ============================================================
        fleet = types.Object()
        fleet.str("frames", label="📊 Frames totales", default=str(summary["total_frames"]),
                   view=types.LabelValueView(read_only=True))
        fleet.str("vehicles", label="🚚 Vehículos activos", default=str(summary["vehicles"]),
                   view=types.LabelValueView(read_only=True))
        fleet.str("drivers", label="🧑‍✈️ Conductores", default=str(summary["drivers"]),
                   view=types.LabelValueView(read_only=True))
        fleet.str("avg_risk", label="⚠️ Riesgo promedio", default=f'{summary["avg_risk"]} / 10',
                   view=types.LabelValueView(read_only=True))
        fleet.str("active_alerts", label="🚨 Alertas activas", default=str(summary["active_alerts"]),
                   view=types.LabelValueView(read_only=True))
        panel.obj("fleet_summary", view=types.GridView(label="Resumen de Flota", columns=5),
                   default=fleet)

        panel.md("divider_1", default="---")

        # ============================================================
        # SECCIÓN 2 — Filtro + Alertas (Hora 2/3, con filtro Hora 4)
        # ============================================================
        filter_obj = types.Object()
        filter_choices = types.Choices()
        for val, lbl in [("all", "Todas"), ("critical", "🔴 Crítico"),
                          ("high", "🟠 Alto"), ("medium", "🟡 Medio"), ("low", "🟢 Bajo")]:
            filter_choices.add_choice(val, label=lbl)
        filter_obj.enum(
            "severity_filter",
            values=filter_choices.values(),
            view=filter_choices,
            default=getattr(ctx.panel.state, "severity_filter", "all"),
            on_change=self.set_severity_filter,
            label="Filtrar por severidad",
        )
        panel.obj("filter_section", view=types.View(label="Filtros"), default=filter_obj)

        alerts_obj = types.Object()
        if alerts:
            for i, alert in enumerate(alerts):
                icon = SEVERITY_ICON.get(alert["severity"], "⚪")
                extra = f' · Recomendación: {alert["recommendation"]}' if alert["recommendation"] else ""
                alerts_obj.str(
                    f"alert_{i}",
                    label=f'{icon} {alert["title"]} — riesgo {alert["risk_score"]}',
                    default=f'{alert["description"]}{extra}',
                    view=types.LabelValueView(read_only=True),
                )
        else:
            alerts_obj.str("no_alerts", label="✅ Sin alertas en este filtro", default="",
                            view=types.LabelValueView(read_only=True))
        panel.obj("alerts_section", view=types.GridView(label="🚨 Alertas activas (ordenadas por riesgo)"),
                   default=alerts_obj)

        panel.md("divider_2", default="---")

        # ============================================================
        # SECCIÓN 3 — Estadísticas de Detección (Hora 2/3)
        # ============================================================
        stats_obj = types.Object()
        for label, count in det_stats.items():
            stats_obj.str(f"stat_{label}", label=f"🔎 {label}", default=str(count),
                           view=types.LabelValueView(read_only=True))
        panel.obj("detection_stats", view=types.GridView(label="📈 Detecciones por categoría", columns=4),
                   default=stats_obj)

        if sev_dist:
            sev_obj = types.Object()
            for sev, count in sev_dist.items():
                icon = SEVERITY_ICON.get(sev, "⚪")
                sev_obj.str(f"sevdist_{sev}", label=f"{icon} {sev}", default=str(count),
                             view=types.LabelValueView(read_only=True))
            panel.obj("severity_distribution", view=types.GridView(label="Distribución de severidad", columns=4),
                       default=sev_obj)

        panel.md("divider_3", default="---")

        # ============================================================
        # SECCIÓN 4 — Estado por vehículo (Hora 4/5 — multi-flota, opcional pero ya soportado)
        # ============================================================
        if fleet_status:
            fleet_obj = types.Object()
            for row in fleet_status:
                color_icon = "🔴" if row["avg_risk"] > 7 else ("🟡" if row["avg_risk"] > 4 else "🟢")
                fleet_obj.str(
                    f"veh_{row['vehicle_id']}",
                    label=f'{color_icon} {row["vehicle_id"]}',
                    default=f'Riesgo prom: {row["avg_risk"]} · Alertas: {row["alerts"]}',
                    view=types.LabelValueView(read_only=True),
                )
            panel.obj("fleet_status", view=types.GridView(label="🚛 Inteligencia colectiva — estado por vehículo"),
                       default=fleet_obj)
            panel.md("divider_4", default="---")

        # ============================================================
        # SECCIÓN 5 — Copiloto (Hora 4)
        # ============================================================
        copiloto = types.Object()
        copiloto.str(
            "last_briefing",
            label="🤖 Último briefing",
            default=getattr(ctx.panel.state, "last_briefing", "Sin briefing aún"),
            view=types.LabelValueView(read_only=True),
        )
        copiloto.btn("run_briefing", label="Generar briefing de ruta", on_click=self.generate_briefing)
        panel.obj("copiloto_section", view=types.GridView(label="Copiloto"), default=copiloto)

        # ============================================================
        # SECCIÓN 6 — Footer / estado del sistema (Hora 5, pulido)
        # ============================================================
        panel.md(
            "footer_md",
            default=(
                "---\n"
                f"**Estado del sistema:** Conectado · "
                f"{summary['total_frames']} frames analizados · "
                f"Última actualización en vivo\n\n"
                "_GUARDIAN — Gestión Unificada de Alertas, Riesgo, Detección e Inteligencia_"
            ),
        )

        return types.Property(
            panel,
            view=types.GridView(
                height=100,
                width=100,
                align_x="center",
                componentsProps={"container": {"sx": {"overflow": "auto", "padding": "12px"}}},
            ),
        )