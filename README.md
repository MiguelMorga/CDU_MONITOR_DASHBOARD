# CDU Monitor Dashboard

Dashboard web en Python para el monitoreo en tiempo real de CDUs mediante SSH,
visualizando temperaturas de aire y líquido a través de una interfaz web.

## Qué hace
- Se conecta vía SSH a múltiples CDUs
- Consulta sensores de temperatura usando command line (CLI)
- Almacena lecturas en memoria por equipo
- Visualiza tendencias de temperatura en tiempo real (últimas 24 horas)
- Muestra el estado de conexión de cada CDU

## Uso
1. Definir las credenciales SSH como variables de entorno
2. Configurar el inventario de IPs en el archivo JSON
3. Ejecutar la aplicación con Streamlit
4. Acceder al dashboard desde el navegador

Ejemplo:
```bash
streamlit run main.py

## Capturas del Dashboard

![All CDU Temperatures](images/all_cdu_temp.png)

![CDU Dashboard](images/cdu_dashboard.png)
