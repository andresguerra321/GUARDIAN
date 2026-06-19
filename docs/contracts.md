# 📊 Contratos de Datos — GUARDIAN

> Fuente de verdad: `shared/contracts.py`
> Solo **Rol 5** modifica los contratos. Los demás importan.

## Objetos Compartidos

### Detection (Centinela → FiftyOne)
| Campo | Tipo | Ejemplo |
|-------|------|---------|
| label | str | `"pedestrian"` |
| confidence | float | `0.87` |
| bounding_box | list[float] | `[0.6, 0.5, 0.05, 0.15]` |
| severity | str | `"high"` |
| description | str | `"Peatón cruzando..."` |

### Alert (Oráculo → Dashboard)
| Campo | Tipo | Ejemplo |
|-------|------|---------|
| id | str | `"AL-a1b2c3d4"` |
| type | str | `"hazard"` |
| severity | str | `"danger"` |
| title | str | `"Peatón en vía"` |
| vehicle_id | str | `"VH-001"` |
| risk_score | float | `7.3` |

### RiskScore (Oráculo)
| Campo | Tipo | Ejemplo |
|-------|------|---------|
| score | float | `7.3` |
| factors | list[str] | `["rain", "night"]` |
| recommendation | str | `"Reducir a 40km/h"` |
| historical_incidents | int | `5` |

## Convenciones
- Campos en **snake_case**
- Timestamps en **ISO 8601**
- Coordenadas: `{"lat": float, "lon": float}`
- Scores: 0-10 (riesgo), 0-1 (confianza/fatiga)
- IDs: `VH-`, `DR-`, `AL-`, `EV-`
