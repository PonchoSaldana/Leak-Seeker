# Leak-Seeker

**Monitoreo en tiempo real** para la detección de anomalías y fugas en sistemas de tuberías utilizando un ensamble de sensores y decisiones basadas en un modelo ded Inteligencia Artificial.

## Descripción del Proyecto
Leak-Seeker es un sistema integral (Hardware + Software) diseñado en el contexto del Genius Arena Hackathon 2026 por nuestro equipo "Los Tlaloques".
Utiliza el microcontrolador Arduino Uno Q  para recopilar datos de 3 diferentes tipos de sensores a un sistema superior (MPU / Edge Impulse) para el análisis de IA. Adicionalmente, cuenta con un dashboard web en tiempo real que permite visualizar la telemetría y el estado de las válvulas de seguridad.

## Arquitectura del Sistema

### 1. Firmware / Hardware (MCU)
El código en C++ (Zephyr OS / Arduino) se divide en varios módulos de sensores especializados:
* **Módulo de Presión (`pt_sensor.h`):** Utiliza sensores MPX5700AP (Upstream y Downstream) leídos a través de un ADC de 12 bits para medir la presión en kPa y calcular diferenciales de caída de presión.
* **Módulo Acústico/Vibración (`vt_sensor.h`):** Integración de un sensor Piezoeléctrico amplificado con LM386 para captar la amplitud de la señal acústica en el tubo y detectar ruidos anómalos de fugas.
* **Módulo de Flujo (`ft_sensor.h`):** Emplea caudalímetros YF-S201 procesados mediante interrupciones de hardware para medir el flujo de agua en Litros por minuto (L/min) y detectar diferenciales por fugas.
* **Módulo de Serialización (`serializacion.h`):** Empaqueta las lecturas (PT01, PT02, VT01, VT02 y diferencial de flujo) en formato CSV a 50Hz para ser transmitidos vía UART (Serial1) y analizados por un modelo de Machine Learning (Edge Impulse).


//imagen

### 2. Software / Dashboard Web
La interfaz y servidor web están construidos con un stack de JavaScript:
* **Backend (`server.js`):** Servidor Node.js utilizando Express y Socket.io para recibir los datos de los sensores (a través de una API REST `/api/data`) y emitirlos en tiempo real a los clientes conectados.
* **Frontend (`index.html` & `style.css`):** Un panel de control intuitivo que muestra:
    * Niveles de vibración.
    * Presión de agua.
    * Flujo de agua.
    * **Acción de IA:** Visualización de las decisiones del modelo, como el cierre automático de la válvula de seguridad ("VÁLVULA CERRADA") en caso de anomalías peligrosas.
    * **Alertas:** Sistema de notificaciones *toast* emergentes para advertir sobre vibración anormal, presión elevada o flujos inconstantes.
