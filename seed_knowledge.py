"""
seed_knowledge.py — Pobla Notion con 22 páginas de ISC.
Uso: python seed_knowledge.py
"""
import os, time
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
PARENT = os.getenv("NOTION_PARENT_PAGE_ID")

# ── helpers de bloques ────────────────────────────────────────────────────────

def rt(text, bold=False, code=False, color="default"):
    ann = {}
    if bold: ann["bold"] = True
    if code: ann["code"] = True
    if color != "default": ann["color"] = color
    obj = {"type": "text", "text": {"content": text}}
    if ann: obj["annotations"] = ann
    return obj

def h1(text):   return {"object":"block","type":"heading_1",  "heading_1":  {"rich_text":[rt(text)]}}
def h2(text):   return {"object":"block","type":"heading_2",  "heading_2":  {"rich_text":[rt(text)]}}
def h3(text):   return {"object":"block","type":"heading_3",  "heading_3":  {"rich_text":[rt(text)]}}
def p(text):    return {"object":"block","type":"paragraph",  "paragraph":  {"rich_text":[rt(text)]}}
def b(text):    return {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[rt(text)]}}
def n(text):    return {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[rt(text)]}}
def div():      return {"object":"block","type":"divider","divider":{}}
def quote(text):return {"object":"block","type":"quote","quote":{"rich_text":[rt(text)]}}
def code(text, lang="plain text"):
    return {"object":"block","type":"code","code":{"rich_text":[rt(text)],"language":lang}}
def callout(text, emoji="💡"):
    return {"object":"block","type":"callout","callout":{"rich_text":[rt(text)],"icon":{"type":"emoji","emoji":emoji}}}
def table(rows, header=True):
    return {"object":"block","type":"table","table":{
        "table_width": len(rows[0]),
        "has_column_header": header,
        "has_row_header": False,
        "children":[{"type":"table_row","table_row":{"cells":[[rt(c)] for c in row]}} for row in rows]
    }}

# ── datos de las 22 páginas ───────────────────────────────────────────────────

PAGINAS = [

# 1
("🔢 Algoritmos y Complejidad Computacional", [
    h1("Algoritmos y Complejidad Computacional"),
    callout("Un algoritmo es un conjunto finito de instrucciones bien definidas para resolver un problema.", "🎯"),
    div(),
    h2("¿Qué es la complejidad computacional?"),
    p("La complejidad computacional mide los recursos (tiempo y espacio) que consume un algoritmo en función del tamaño de la entrada n."),
    h2("Notación Big-O"),
    p("Big-O describe el peor caso del comportamiento de un algoritmo:"),
    table([
        ["Notación","Nombre","Ejemplo"],
        ["O(1)","Constante","Acceso a arreglo por índice"],
        ["O(log n)","Logarítmica","Búsqueda binaria"],
        ["O(n)","Lineal","Recorrido de lista"],
        ["O(n log n)","Cuasi-lineal","Merge Sort, Heap Sort"],
        ["O(n²)","Cuadrática","Bubble Sort, Selection Sort"],
        ["O(2ⁿ)","Exponencial","Subconjuntos de un conjunto"],
        ["O(n!)","Factorial","Permutaciones (TSP fuerza bruta)"],
    ]),
    div(),
    h2("Algoritmos de ordenamiento"),
    b("Bubble Sort — O(n²) promedio y peor caso. Simple pero ineficiente."),
    b("Merge Sort — O(n log n) garantizado. Divide y vencerás. Estable."),
    b("Quick Sort — O(n log n) promedio, O(n²) peor caso. Muy usado en práctica."),
    b("Heap Sort — O(n log n) garantizado. No estable. In-place."),
    b("Counting Sort — O(n+k). Solo funciona con enteros en rango conocido."),
    div(),
    h2("Ejemplo: Búsqueda binaria"),
    code("""def busqueda_binaria(arr, target):
    izq, der = 0, len(arr) - 1
    while izq <= der:
        mid = (izq + der) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            izq = mid + 1
        else:
            der = mid - 1
    return -1  # No encontrado""", "python"),
    callout("Para un arreglo de 1,000,000 elementos, la búsqueda binaria necesita máximo 20 comparaciones. La lineal necesita 1,000,000.", "⚡"),
]),

# 2
("🌳 Estructuras de Datos", [
    h1("Estructuras de Datos"),
    p("Las estructuras de datos organizan y almacenan información para que pueda ser accedida y modificada eficientemente."),
    div(),
    h2("Estructuras lineales"),
    table([
        ["Estructura","Acceso","Inserción","Eliminación","Uso típico"],
        ["Array","O(1)","O(n)","O(n)","Buffer, matrices"],
        ["Lista enlazada","O(n)","O(1)","O(1)","Listas dinámicas"],
        ["Pila (Stack)","O(n)","O(1)","O(1)","Historial, expresiones"],
        ["Cola (Queue)","O(n)","O(1)","O(1)","BFS, tareas en espera"],
        ["Deque","O(n)","O(1)","O(1)","Sliding window"],
    ]),
    div(),
    h2("Estructuras no lineales"),
    h3("Árboles"),
    b("Árbol Binario de Búsqueda (BST) — búsqueda O(log n) promedio."),
    b("Árbol AVL — BST autobalanceado. Garantiza O(log n) siempre."),
    b("Árbol Rojo-Negro — usado en std::map de C++ y TreeMap de Java."),
    b("Heap (Min/Max) — acceso al mínimo/máximo en O(1). Base de colas de prioridad."),
    b("Trie — búsqueda de prefijos en O(m) donde m es la longitud de la cadena."),
    h3("Grafos"),
    b("Representación por lista de adyacencia — eficiente en memoria para grafos dispersos."),
    b("Representación por matriz de adyacencia — acceso O(1) a aristas. Costoso en memoria."),
    div(),
    h2("Tabla Hash"),
    p("Mapea claves a valores usando una función hash. Operaciones en O(1) promedio."),
    b("Colisiones se resuelven por encadenamiento (chaining) o sondeo abierto (open addressing)."),
    b("Factor de carga: cuando supera ~0.75 se rehashea para mantener rendimiento."),
    code("""# Ejemplo: tabla hash en Python (dict)
frecuencia = {}
for palabra in texto.split():
    frecuencia[palabra] = frecuencia.get(palabra, 0) + 1""", "python"),
]),

# 3
("🗄️ Bases de Datos Relacionales", [
    h1("Bases de Datos Relacionales"),
    callout("Una base de datos relacional organiza la información en tablas con filas y columnas, relacionadas entre sí mediante llaves.", "🗄️"),
    div(),
    h2("Conceptos fundamentales"),
    b("Tabla (Relación) — colección de filas (tuplas) con las mismas columnas (atributos)."),
    b("Llave Primaria (PK) — identificador único de cada fila."),
    b("Llave Foránea (FK) — referencia a la PK de otra tabla."),
    b("Índice — estructura auxiliar que acelera las búsquedas."),
    div(),
    h2("Normalización"),
    table([
        ["Forma Normal","Requisito"],
        ["1FN","Valores atómicos, sin grupos repetidos"],
        ["2FN","1FN + sin dependencias parciales de la PK"],
        ["3FN","2FN + sin dependencias transitivas"],
        ["BCNF","Todo determinante es llave candidata"],
    ]),
    div(),
    h2("SQL básico"),
    code("""-- Crear tabla
CREATE TABLE estudiante (
    id        INT PRIMARY KEY AUTO_INCREMENT,
    nombre    VARCHAR(100) NOT NULL,
    matricula VARCHAR(20)  UNIQUE,
    carrera   VARCHAR(50)
);

-- Consulta con JOIN
SELECT e.nombre, c.titulo
FROM   estudiante e
JOIN   inscripcion i ON e.id = i.estudiante_id
JOIN   curso      c ON i.curso_id = c.id
WHERE  e.carrera = 'ISC'
ORDER  BY e.nombre;""", "sql"),
    div(),
    h2("Transacciones y ACID"),
    b("Atomicidad — una transacción se ejecuta completa o no se ejecuta."),
    b("Consistencia — la BD pasa de un estado válido a otro estado válido."),
    b("Aislamiento — transacciones concurrentes no interfieren entre sí."),
    b("Durabilidad — los cambios confirmados persisten aunque haya fallo."),
]),

# 4
("🧩 Programación Orientada a Objetos", [
    h1("Programación Orientada a Objetos (POO)"),
    p("Paradigma que organiza el software en objetos que combinan estado (atributos) y comportamiento (métodos)."),
    div(),
    h2("Los 4 pilares"),
    table([
        ["Pilar","Descripción","Ejemplo"],
        ["Encapsulamiento","Ocultar detalles internos, exponer solo lo necesario","Getters y setters"],
        ["Abstracción","Modelar solo las características relevantes","Clase abstracta Animal"],
        ["Herencia","Una clase hereda atributos y métodos de otra","Gato extends Animal"],
        ["Polimorfismo","Un objeto se comporta de formas distintas según el contexto","método sonido() distinto por clase"],
    ]),
    div(),
    h2("Patrones de diseño más comunes"),
    h3("Creacionales"),
    b("Singleton — garantiza una sola instancia de una clase."),
    b("Factory Method — delega la creación de objetos a subclases."),
    b("Builder — construye objetos complejos paso a paso."),
    h3("Estructurales"),
    b("Adapter — permite que interfaces incompatibles trabajen juntas."),
    b("Decorator — agrega funcionalidad a objetos sin modificar su clase."),
    b("Facade — simplifica una interfaz compleja con una interfaz más simple."),
    h3("Comportamiento"),
    b("Observer — define dependencia uno a muchos entre objetos."),
    b("Strategy — define una familia de algoritmos intercambiables."),
    b("Command — encapsula una solicitud como un objeto."),
    div(),
    h2("Principios SOLID"),
    n("S — Single Responsibility: una clase, una responsabilidad."),
    n("O — Open/Closed: abierto para extensión, cerrado para modificación."),
    n("L — Liskov Substitution: objetos de subclase deben sustituir a los de la clase base."),
    n("I — Interface Segregation: interfaces específicas mejor que una interfaz general."),
    n("D — Dependency Inversion: depender de abstracciones, no de implementaciones."),
]),

# 5
("💻 Sistemas Operativos", [
    h1("Sistemas Operativos"),
    p("Un SO gestiona el hardware del computador y proporciona servicios a los programas de usuario."),
    callout("Ejemplos: Linux, Windows, macOS, Android, iOS.", "🖥️"),
    div(),
    h2("Componentes principales"),
    b("Kernel — núcleo del SO. Gestiona memoria, procesos, E/S y sistema de archivos."),
    b("Shell — interfaz entre usuario y kernel (bash, zsh, PowerShell)."),
    b("Sistema de archivos — organización jerárquica de datos (NTFS, ext4, APFS)."),
    b("Drivers — traducen llamadas del SO a instrucciones de hardware."),
    div(),
    h2("Gestión de procesos"),
    table([
        ["Estado","Descripción"],
        ["Nuevo","El proceso acaba de crearse"],
        ["Listo","Espera turno de CPU"],
        ["En ejecución","Actualmente usando la CPU"],
        ["Bloqueado","Esperando un evento (E/S, semáforo)"],
        ["Terminado","Proceso finalizado"],
    ]),
    h3("Algoritmos de planificación (scheduling)"),
    b("FCFS — First Come First Served. Simple, puede causar convoy effect."),
    b("SJF — Shortest Job First. Minimiza tiempo promedio de espera."),
    b("Round Robin — turno fijo (quantum) por proceso. Justo y predecible."),
    b("Prioridades — procesos con mayor prioridad ejecutan primero. Riesgo de inanición."),
    div(),
    h2("Gestión de memoria"),
    b("Memoria virtual — ilusión de más RAM usando disco (swap)."),
    b("Paginación — divide memoria en páginas de tamaño fijo. Elimina fragmentación externa."),
    b("Segmentación — divide en segmentos de tamaño variable (código, datos, pila)."),
    b("TLB (Translation Lookaside Buffer) — caché para acelerar traducción de direcciones virtuales."),
    div(),
    h2("Deadlock"),
    p("Condición donde dos o más procesos se bloquean mutuamente esperando recursos. Condiciones de Coffman:"),
    n("Exclusión mutua — el recurso solo puede usarlo un proceso a la vez."),
    n("Retención y espera — proceso retiene recursos mientras espera otros."),
    n("No apropiación — los recursos no pueden quitarse forzadamente."),
    n("Espera circular — cadena de procesos esperando recursos del siguiente."),
]),

# 6
("🌐 Redes de Computadoras", [
    h1("Redes de Computadoras"),
    p("Sistema que permite la comunicación e intercambio de datos entre computadoras."),
    div(),
    h2("Modelo OSI (7 capas)"),
    table([
        ["Capa","Nombre","Protocolo/Ejemplo"],
        ["7","Aplicación","HTTP, FTP, SMTP, DNS"],
        ["6","Presentación","SSL/TLS, JPEG, ASCII"],
        ["5","Sesión","NetBIOS, RPC"],
        ["4","Transporte","TCP, UDP"],
        ["3","Red","IP, ICMP, ARP"],
        ["2","Enlace de datos","Ethernet, Wi-Fi (802.11)"],
        ["1","Física","Cable, fibra óptica, señal de radio"],
    ]),
    div(),
    h2("TCP vs UDP"),
    table([
        ["Característica","TCP","UDP"],
        ["Conexión","Orientado a conexión","Sin conexión"],
        ["Confiabilidad","Garantiza entrega","Sin garantía"],
        ["Orden","Mantiene orden","Sin orden garantizado"],
        ["Velocidad","Más lento","Más rápido"],
        ["Uso","HTTP, FTP, SSH","DNS, streaming, juegos online"],
    ]),
    div(),
    h2("Direccionamiento IP"),
    b("IPv4 — 32 bits (4,294,967,296 direcciones). Ej: 192.168.1.1"),
    b("IPv6 — 128 bits. Ej: 2001:0db8:85a3::8a2e:0370:7334"),
    b("Máscara de subred — define la porción de red vs host. Ej: /24 = 255.255.255.0"),
    b("NAT — permite que múltiples dispositivos compartan una IP pública."),
    div(),
    h2("Protocolos de aplicación"),
    b("HTTP/HTTPS — transferencia de hipertexto. Puerto 80/443."),
    b("DNS — traduce nombres de dominio a IPs. Puerto 53."),
    b("DHCP — asigna IPs automáticamente. Puerto 67/68."),
    b("SSH — acceso seguro remoto. Puerto 22."),
    b("SMTP/IMAP/POP3 — correo electrónico."),
]),

# 7
("⚙️ Arquitectura de Computadoras", [
    h1("Arquitectura de Computadoras"),
    p("Describe la organización, estructura y funciones de los componentes de un sistema de cómputo."),
    div(),
    h2("Modelo de Von Neumann"),
    b("Unidad Central de Procesamiento (CPU) — ejecuta instrucciones."),
    b("Memoria principal (RAM) — almacena datos e instrucciones en ejecución."),
    b("Dispositivos de E/S — teclado, monitor, disco, red."),
    b("Bus del sistema — vías de comunicación entre componentes."),
    callout("La arquitectura Harvard separa memoria de instrucciones y datos. Usada en microcontroladores.", "🔬"),
    div(),
    h2("La CPU"),
    h3("Componentes"),
    b("ALU (Arithmetic Logic Unit) — realiza operaciones aritméticas y lógicas."),
    b("Unidad de control — decodifica instrucciones y coordina la ejecución."),
    b("Registros — almacenamiento ultra-rápido dentro del CPU."),
    b("Caché L1/L2/L3 — memorias intermedias para reducir latencia de acceso a RAM."),
    h3("Pipeline de instrucciones"),
    n("Fetch — traer la instrucción de memoria."),
    n("Decode — decodificar qué operación realizar."),
    n("Execute — ejecutar la operación en la ALU."),
    n("Write-back — escribir el resultado al registro o memoria."),
    div(),
    h2("Jerarquía de memoria"),
    table([
        ["Nivel","Tipo","Velocidad","Capacidad","Costo"],
        ["1","Registros","< 1 ns","< 1 KB","Muy alto"],
        ["2","Caché L1","~1 ns","32-64 KB","Alto"],
        ["3","Caché L2/L3","~5 ns","256 KB - 32 MB","Moderado"],
        ["4","RAM","~60 ns","4-64 GB","Bajo"],
        ["5","SSD","~100 µs","256 GB - 4 TB","Muy bajo"],
        ["6","HDD","~10 ms","1-20 TB","Mínimo"],
    ]),
]),

# 8
("📐 Ingeniería de Software", [
    h1("Ingeniería de Software"),
    p("Disciplina que aplica principios de ingeniería al desarrollo, operación y mantenimiento de software."),
    div(),
    h2("Ciclo de vida del software (SDLC)"),
    n("Análisis de requisitos — qué debe hacer el sistema."),
    n("Diseño del sistema — cómo se construirá."),
    n("Implementación (codificación)."),
    n("Pruebas — verificar y validar."),
    n("Despliegue."),
    n("Mantenimiento — correcciones y mejoras."),
    div(),
    h2("Modelos de proceso"),
    table([
        ["Modelo","Características","Cuándo usarlo"],
        ["Cascada","Fases secuenciales sin retroceso","Requisitos bien definidos y estables"],
        ["Espiral","Ciclos iterativos con gestión de riesgo","Proyectos grandes y riesgosos"],
        ["Ágil","Iteraciones cortas (sprints), entrega continua","Requisitos cambiantes"],
        ["RUP","4 fases: inicio, elaboración, construcción, transición","Proyectos empresariales"],
    ]),
    div(),
    h2("UML — Diagramas más usados"),
    b("Diagrama de Casos de Uso — qué hace el sistema, quién lo usa."),
    b("Diagrama de Clases — estructura estática: clases, atributos, relaciones."),
    b("Diagrama de Secuencia — interacción entre objetos en el tiempo."),
    b("Diagrama de Actividades — flujo de trabajo / algoritmos."),
    b("Diagrama de Componentes — estructura física del software."),
    b("Diagrama de Despliegue — distribución física en hardware."),
    div(),
    callout("La deuda técnica acumulada por malas decisiones de diseño puede costar más en mantenimiento que el desarrollo original.", "⚠️"),
]),

# 9
("🌍 Desarrollo Web Full Stack", [
    h1("Desarrollo Web Full Stack"),
    p("Abarca tanto el lado del cliente (frontend) como el servidor (backend) y la base de datos."),
    div(),
    h2("Frontend"),
    h3("Tecnologías base"),
    b("HTML5 — estructura y semántica del contenido."),
    b("CSS3 — estilos, animaciones, diseño responsive (Flexbox, Grid)."),
    b("JavaScript — interactividad, manipulación del DOM, llamadas a APIs."),
    h3("Frameworks y librerías"),
    b("React — librería de UI basada en componentes. Desarrollada por Meta."),
    b("Vue.js — framework progresivo, curva de aprendizaje suave."),
    b("Angular — framework completo de Google. Usa TypeScript."),
    b("Next.js / Nuxt — SSR (Server-Side Rendering) para React/Vue."),
    div(),
    h2("Backend"),
    table([
        ["Tecnología","Lenguaje","Puntos fuertes"],
        ["Node.js / Express","JavaScript","Alta concurrencia, ecosistema npm"],
        ["Django","Python","Baterías incluidas, ORM potente"],
        ["FastAPI","Python","Alto rendimiento, tipado, async"],
        ["Spring Boot","Java","Robusto, enterprise, microservicios"],
        ["Laravel","PHP","Eloquent ORM, Blade templates"],
    ]),
    div(),
    h2("REST API — principios"),
    b("Recursos identificados por URLs (ej. /api/usuarios/42)."),
    b("Verbos HTTP: GET (leer), POST (crear), PUT/PATCH (actualizar), DELETE (eliminar)."),
    b("Sin estado (stateless) — cada request contiene toda la información necesaria."),
    b("Respuestas en JSON. Códigos de estado HTTP semánticos (200, 201, 404, 500)."),
    div(),
    h2("Herramientas del ecosistema"),
    b("Git/GitHub — control de versiones."),
    b("Docker — contenedorización para entornos reproducibles."),
    b("CI/CD — automatización de pruebas y despliegues (GitHub Actions, Jenkins)."),
    b("Postman / Insomnia — prueba de APIs."),
]),

# 10
("🤖 Inteligencia Artificial y Machine Learning", [
    h1("Inteligencia Artificial y Machine Learning"),
    callout("IA es el campo; ML es la técnica más usada hoy; Deep Learning es un subconjunto de ML.", "🧠"),
    div(),
    h2("Tipos de aprendizaje automático"),
    table([
        ["Tipo","Descripción","Ejemplos"],
        ["Supervisado","Aprende de datos etiquetados","Clasificación, regresión"],
        ["No supervisado","Encuentra patrones en datos sin etiquetar","Clustering, reducción de dimensionalidad"],
        ["Por refuerzo","Aprende por ensayo y error con recompensas","Juegos, robótica, trading"],
        ["Semi-supervisado","Combina pocos datos etiquetados con muchos sin etiquetar","Clasificación de texto"],
    ]),
    div(),
    h2("Algoritmos clásicos"),
    b("Regresión lineal / logística — predicción de valores continuos / clases binarias."),
    b("Árboles de decisión y Random Forest — clasificación robusta y explicable."),
    b("SVM (Support Vector Machine) — clasifica con máximo margen."),
    b("K-Means — agrupa datos en K clusters."),
    b("KNN (K-Nearest Neighbors) — clasifica según los K vecinos más cercanos."),
    div(),
    h2("Redes Neuronales Artificiales"),
    n("Capa de entrada — recibe los datos crudos."),
    n("Capas ocultas — transformaciones no lineales (ReLU, sigmoid, tanh)."),
    n("Capa de salida — produce la predicción final."),
    b("Backpropagation — calcula gradientes y actualiza pesos."),
    b("Overfitting — el modelo memoriza entrenamiento pero falla en datos nuevos."),
    b("Regularización (dropout, L1/L2) — técnicas para reducir overfitting."),
    div(),
    h2("Deep Learning y aplicaciones"),
    b("CNN (Convolutional Neural Net) — visión computacional, clasificación de imágenes."),
    b("RNN / LSTM — procesamiento de secuencias, predicción de series temporales."),
    b("Transformer — base de GPT, BERT, LLaMA. Dominante en NLP."),
    b("Modelos de difusión — generación de imágenes (Stable Diffusion, DALL-E)."),
    code("""# Ejemplo mínimo con scikit-learn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
modelo = RandomForestClassifier(n_estimators=100)
modelo.fit(X_train, y_train)
print("Precisión:", modelo.score(X_test, y_test))""", "python"),
]),

# 11
("🔐 Ciberseguridad y Criptografía", [
    h1("Ciberseguridad y Criptografía"),
    p("La ciberseguridad protege sistemas, redes y datos de ataques, daños o acceso no autorizado."),
    div(),
    h2("Pilares de la seguridad — CIA"),
    b("Confidencialidad — solo usuarios autorizados acceden a la información."),
    b("Integridad — la información no ha sido alterada sin autorización."),
    b("Disponibilidad — el sistema está accesible cuando se necesita."),
    div(),
    h2("Vulnerabilidades OWASP Top 10 (2021)"),
    n("Broken Access Control — control de acceso roto."),
    n("Cryptographic Failures — cifrado débil o ausente."),
    n("Injection — SQL, NoSQL, OS, LDAP injection."),
    n("Insecure Design — diseño sin modelado de amenazas."),
    n("Security Misconfiguration — configuración incorrecta."),
    n("Vulnerable and Outdated Components."),
    n("Identification and Authentication Failures."),
    n("Software and Data Integrity Failures."),
    n("Security Logging and Monitoring Failures."),
    n("Server-Side Request Forgery (SSRF)."),
    div(),
    h2("Criptografía"),
    table([
        ["Tipo","Ejemplo","Uso"],
        ["Simétrica","AES-256, ChaCha20","Cifrado de datos en reposo"],
        ["Asimétrica","RSA-2048, ECC","TLS, firmas digitales, SSH"],
        ["Hash","SHA-256, bcrypt","Contraseñas, integridad de archivos"],
        ["HMAC","HMAC-SHA256","Autenticación de mensajes (JWT)"],
    ]),
    div(),
    callout("Nunca almacenes contraseñas en texto plano. Usa bcrypt, Argon2 o scrypt con salt.", "🔑"),
    h2("Autenticación moderna"),
    b("JWT (JSON Web Token) — token firmado que contiene claims del usuario."),
    b("OAuth 2.0 — protocolo de autorización delegada (Google, GitHub, Facebook login)."),
    b("MFA (Multi-Factor Authentication) — combina algo que sabes, tienes y eres."),
    b("Zero Trust — nunca confiar, siempre verificar. Incluso dentro de la red interna."),
]),

# 12
("☁️ Cloud Computing y DevOps", [
    h1("Cloud Computing y DevOps"),
    div(),
    h2("Modelos de servicio en la nube"),
    table([
        ["Modelo","Responsabilidad cliente","Ejemplos"],
        ["IaaS","OS, middleware, runtime, app","AWS EC2, GCP Compute, Azure VM"],
        ["PaaS","Solo la aplicación y datos","Heroku, App Engine, Azure App Service"],
        ["SaaS","Solo configurar y usar","Gmail, Salesforce, Office 365"],
        ["FaaS/Serverless","Solo el código de la función","AWS Lambda, Cloud Functions"],
    ]),
    div(),
    h2("DevOps — cultura y prácticas"),
    p("DevOps une desarrollo (Dev) y operaciones (Ops) para entregar software más rápido y con mayor calidad."),
    h3("Pipeline CI/CD"),
    n("Commit — desarrollador sube código a repositorio."),
    n("Build — compilación y construcción de la aplicación."),
    n("Test — pruebas unitarias, integración, end-to-end."),
    n("Deploy to staging — despliegue en ambiente de prueba."),
    n("Deploy to production — despliegue automático si todo pasa."),
    div(),
    h2("Contenedores y orquestación"),
    b("Docker — empaquetar aplicación con sus dependencias en un contenedor."),
    b("Docker Compose — orquestar múltiples contenedores localmente."),
    b("Kubernetes (K8s) — orquestación de contenedores en producción a escala."),
    b("Helm — gestor de paquetes para Kubernetes."),
    div(),
    h2("Infraestructura como Código (IaC)"),
    b("Terraform — define infraestructura en HCL. Multi-nube."),
    b("Ansible — automatización de configuración. Agentless."),
    b("AWS CloudFormation / Azure ARM — específicos de cada nube."),
    code("""# Ejemplo Dockerfile para una app Python
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]""", "bash"),
]),

# 13
("📝 Lenguajes de Programación", [
    h1("Lenguajes de Programación"),
    p("Formal language que permite a los programadores comunicar instrucciones a una computadora."),
    div(),
    h2("Paradigmas"),
    table([
        ["Paradigma","Descripción","Lenguajes"],
        ["Imperativo","Secuencia de instrucciones que cambian el estado","C, Pascal, Assembly"],
        ["Orientado a Objetos","Modela usando objetos con estado y comportamiento","Java, C++, Python, C#"],
        ["Funcional","Funciones puras, inmutabilidad, sin efectos secundarios","Haskell, Erlang, Clojure, F#"],
        ["Lógico","Describe hechos y reglas, el motor infiere conclusiones","Prolog"],
        ["Multiparadigma","Soporta varios paradigmas","Python, Scala, Kotlin, Rust"],
    ]),
    div(),
    h2("Tipado"),
    b("Estático — tipos verificados en compilación. Java, C++, Rust, TypeScript."),
    b("Dinámico — tipos verificados en ejecución. Python, JavaScript, Ruby."),
    b("Fuertemente tipado — no permite conversiones implícitas peligrosas. Python."),
    b("Débilmente tipado — permite coerciones implícitas. JavaScript, C."),
    div(),
    h2("Comparativa de lenguajes populares en ISC"),
    table([
        ["Lenguaje","Uso principal","Fortaleza"],
        ["Python","IA/ML, scripting, backend","Legible, ecosistema enorme"],
        ["Java","Enterprise, Android","Portabilidad, OOP sólido"],
        ["C/C++","Sistemas, embebidos, juegos","Rendimiento, control total"],
        ["JavaScript","Web, Node.js, móvil","Ubicuo, async/await"],
        ["Rust","Sistemas, WebAssembly","Seguridad de memoria sin GC"],
        ["Go","Microservicios, CLI tools","Concurrencia, compilación rápida"],
        ["SQL","Bases de datos","Consultas declarativas"],
    ]),
]),

# 14
("🔧 Compiladores e Intérpretes", [
    h1("Compiladores e Intérpretes"),
    p("Programas que traducen código fuente a otro lenguaje (compilador) o lo ejecutan directamente (intérprete)."),
    div(),
    h2("Fases de un compilador"),
    n("Análisis léxico (Scanner) — divide el código en tokens."),
    n("Análisis sintáctico (Parser) — verifica que los tokens forman estructuras válidas (árbol de parse)."),
    n("Análisis semántico — verifica tipos, declaraciones, reglas semánticas."),
    n("Generación de código intermedio — representación independiente de la arquitectura."),
    n("Optimización — mejora el código intermedio."),
    n("Generación de código objeto — código máquina o ensamblador."),
    div(),
    h2("Tokens comunes"),
    table([
        ["Token","Ejemplo"],
        ["KEYWORD","if, while, int, return"],
        ["IDENTIFIER","nombre_variable, myFunc"],
        ["NUMBER","42, 3.14, 0xFF"],
        ["STRING","\"Hola mundo\""],
        ["OPERATOR","+ - * / == !="],
        ["DELIMITER","( ) { } ; ,"],
    ]),
    div(),
    h2("Comparación Compilador vs Intérprete"),
    table([
        ["Aspecto","Compilador","Intérprete"],
        ["Traducción","Todo el programa antes de ejecutar","Línea por línea durante ejecución"],
        ["Velocidad","Más rápido en ejecución","Más lento (overhead de interpretación)"],
        ["Detección de errores","Antes de ejecutar","Durante ejecución"],
        ["Ejemplos","C, C++, Rust, Go","Python, Ruby, JavaScript"],
    ]),
    callout("JVM de Java y V8 de JavaScript usan JIT (Just-In-Time compilation) que combina ventajas de ambos enfoques.", "⚡"),
]),

# 15
("🔗 Sistemas Distribuidos", [
    h1("Sistemas Distribuidos"),
    p("Colección de computadoras independientes que aparecen al usuario como un sistema único coherente."),
    div(),
    h2("Teorema CAP"),
    callout("Un sistema distribuido puede garantizar máximo 2 de 3 propiedades: Consistencia, Disponibilidad, Tolerancia a Particiones.", "⚠️"),
    table([
        ["Combinación","Sistemas que la usan"],
        ["CP (Consistencia + Particiones)","HBase, ZooKeeper, MongoDB (modo estricto)"],
        ["AP (Disponibilidad + Particiones)","DynamoDB, Cassandra, CouchDB"],
        ["CA (Consistencia + Disponibilidad)","Solo posible sin particiones de red (sistemas locales)"],
    ]),
    div(),
    h2("Arquitectura de Microservicios"),
    b("Cada servicio tiene una responsabilidad específica y puede desplegarse independientemente."),
    b("Comunicación via APIs REST, gRPC o mensajería asíncrona (Kafka, RabbitMQ)."),
    b("API Gateway — punto de entrada único que enruta a los microservicios."),
    b("Service Mesh (Istio, Linkerd) — gestiona comunicación, observabilidad y seguridad."),
    div(),
    h2("Consistencia eventual"),
    p("En sistemas AP, los nodos convergen al mismo estado eventualmente, no instantáneamente."),
    b("Replicación — copias del dato en múltiples nodos para disponibilidad y rendimiento."),
    b("Particionamiento (Sharding) — distribuir datos entre nodos para escalar horizontalmente."),
    b("Vector Clocks — mecanismo para rastrear causalidad y detectar conflictos."),
    div(),
    h2("Patrones de resiliencia"),
    b("Circuit Breaker — corta requests a un servicio fallido para evitar cascada de fallos."),
    b("Retry con backoff exponencial — reintenta con esperas crecientes."),
    b("Bulkhead — aísla fallas para que no afecten todo el sistema."),
    b("Health Check — endpoint /health para monitoreo y load balancers."),
]),

# 16
("∑ Matemáticas Discretas", [
    h1("Matemáticas Discretas"),
    p("Estudia estructuras matemáticas que son fundamentalmente discretas (no continuas), base teórica de la computación."),
    div(),
    h2("Lógica proposicional"),
    table([
        ["Operador","Símbolo","Descripción"],
        ["Negación","¬p","No p"],
        ["Conjunción","p ∧ q","p Y q"],
        ["Disyunción","p ∨ q","p O q"],
        ["Condicional","p → q","Si p entonces q"],
        ["Bicondicional","p ↔ q","p si y solo si q"],
        ["XOR","p ⊕ q","p O exclusivo q"],
    ]),
    div(),
    h2("Teoría de conjuntos"),
    b("Unión A ∪ B — elementos en A, B, o ambos."),
    b("Intersección A ∩ B — elementos en A y en B."),
    b("Diferencia A - B — elementos en A pero no en B."),
    b("Complemento Ā — elementos que no están en A."),
    b("Producto cartesiano A × B — todos los pares ordenados (a, b)."),
    div(),
    h2("Teoría de grafos (conceptos)"),
    b("Grafo G = (V, E) donde V = vértices, E = aristas."),
    b("Grado de un vértice — número de aristas incidentes."),
    b("Camino — secuencia de vértices conectados por aristas."),
    b("Ciclo — camino que empieza y termina en el mismo vértice."),
    b("Árbol de expansión — subgrafo que conecta todos los vértices sin ciclos."),
    div(),
    h2("Combinatoria básica"),
    b("Permutaciones P(n,r) = n! / (n-r)! — arreglos ordenados de r elementos de n."),
    b("Combinaciones C(n,r) = n! / (r! × (n-r)!) — selecciones sin orden."),
    b("Principio de inclusión-exclusión: |A ∪ B| = |A| + |B| - |A ∩ B|."),
    b("Principio de la paloma: si n+1 palomas en n nidos, al menos 2 palomas comparten nido."),
]),

# 17
("📊 Álgebra Lineal Aplicada a Computación", [
    h1("Álgebra Lineal Aplicada a Computación"),
    p("Estudia vectores, matrices y transformaciones lineales. Es la base matemática del Machine Learning, Gráficos 3D y más."),
    div(),
    h2("Vectores"),
    b("Vector — arreglo ordenado de números. Representa dirección y magnitud."),
    b("Magnitud (norma) ||v|| = √(v₁² + v₂² + ... + vₙ²)."),
    b("Producto punto (dot product) u·v = Σ uᵢvᵢ. Mide similitud entre vectores."),
    b("Cosine similarity — mide ángulo entre vectores. Base de motores de búsqueda y NLP."),
    div(),
    h2("Matrices"),
    b("Multiplicación de matrices — base de transformaciones y redes neuronales."),
    b("Matriz transpuesta Aᵀ — intercambia filas y columnas."),
    b("Matriz inversa A⁻¹ — tal que A × A⁻¹ = I. Usada para resolver sistemas lineales."),
    b("Determinante — escalar que indica si la matriz es invertible (det ≠ 0)."),
    div(),
    h2("Aplicaciones en computación"),
    table([
        ["Aplicación","Uso del álgebra lineal"],
        ["Redes neuronales","Multiplicación de matrices en cada capa"],
        ["Computer Graphics","Transformaciones 3D (rotación, escala, proyección)"],
        ["Compresión de imágenes","SVD (Descomposición en valores singulares)"],
        ["Motores de búsqueda","TF-IDF vectores de documentos, cosine similarity"],
        ["Criptografía","Matrices en cifrados como Hill Cipher"],
        ["Sistemas de recomendación","Factorización matricial (Netflix Prize)"],
    ]),
    div(),
    h2("Eigenvalores y Eigenvectores"),
    p("Av = λv, donde λ es el eigenvalor y v el eigenvector. Fundamentales en PCA y análisis espectral de grafos."),
    callout("PCA (Principal Component Analysis) usa eigenvectores para reducir dimensionalidad manteniendo la mayor varianza.", "💡"),
]),

# 18
("🤖 Teoría de Autómatas y Lenguajes Formales", [
    h1("Teoría de Autómatas y Lenguajes Formales"),
    p("Estudia modelos abstractos de computación y las clases de lenguajes que cada modelo puede reconocer."),
    div(),
    h2("Jerarquía de Chomsky"),
    table([
        ["Tipo","Gramática","Autómata","Lenguaje"],
        ["Tipo 0","Sin restricciones","Máquina de Turing","Recursivamente enumerables"],
        ["Tipo 1","Sensible al contexto","LBA (Automata acotado)","Sensibles al contexto"],
        ["Tipo 2","Libre de contexto","Autómata de pila","Libres de contexto"],
        ["Tipo 3","Regular","Autómata finito","Regulares"],
    ]),
    div(),
    h2("Autómata Finito Determinista (DFA)"),
    b("M = (Q, Σ, δ, q₀, F) donde Q=estados, Σ=alfabeto, δ=función de transición."),
    b("Acepta una cadena si termina en un estado final después de leerla completa."),
    b("Aplicación directa: lexers de compiladores, validación de expresiones regulares."),
    div(),
    h2("Expresiones Regulares (RegEx)"),
    table([
        ["Símbolo","Significado","Ejemplo"],
        ["a","Literal, coincide con 'a'","a"],
        ["a|b","Alternación: a o b","gato|perro"],
        ["a*","Kleene star: 0 o más repeticiones","a*"],
        ["a+","1 o más repeticiones","a+"],
        ["a?","0 o 1 ocurrencia (opcional)","colou?r"],
        ["[abc]","Clase de caracteres","[0-9]"],
        ["^...$","Anclas inicio y fin","^[a-z]+$"],
    ]),
    code(r"""import re
# Validar correo electrónico mexicano
patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
print(re.match(patron, 'juan@tec.mx'))  # Match!""", "python"),
    div(),
    h2("Gramáticas Libres de Contexto (CFG)"),
    p("Usadas para describir la sintaxis de lenguajes de programación. Parsers como LL(1), LR(0), LALR los procesan."),
    b("Producción ejemplo: E → E + T | T ; T → T * F | F ; F → (E) | num"),
]),

# 19
("🎨 Diseño de Interfaces y UX", [
    h1("Diseño de Interfaces y UX"),
    p("UX (User Experience) engloba todos los aspectos de la interacción del usuario con el sistema."),
    div(),
    h2("Principios de usabilidad — Jakob Nielsen"),
    n("Visibilidad del estado — el sistema siempre informa qué está pasando."),
    n("Match con el mundo real — lenguaje del usuario, no del sistema."),
    n("Control y libertad — deshacer y rehacer siempre disponibles."),
    n("Consistencia — mismas acciones producen mismos resultados."),
    n("Prevención de errores — mejor que mensajes de error."),
    n("Reconocimiento sobre recuerdo — minimizar carga cognitiva."),
    n("Flexibilidad — atajos para usuarios expertos."),
    n("Diseño minimalista — sin información irrelevante."),
    n("Ayuda al recuperarse de errores — mensajes claros y soluciones."),
    n("Documentación y ayuda accesible."),
    div(),
    h2("Proceso de diseño UX"),
    b("Research — entrevistas a usuarios, análisis de competencia."),
    b("Ideación — brainstorming, card sorting, user stories."),
    b("Prototipado — wireframes (baja fidelidad) → mockups (alta fidelidad)."),
    b("Pruebas de usabilidad — observar a usuarios reales usando el sistema."),
    b("Iteración — refinar basándose en feedback."),
    div(),
    h2("Herramientas"),
    table([
        ["Herramienta","Uso"],
        ["Figma","Diseño UI/UX colaborativo, prototipado"],
        ["Adobe XD","Diseño y prototipado de experiencias"],
        ["Sketch","Diseño UI para macOS"],
        ["InVision","Prototipado y feedback de equipos"],
        ["Zeplin","Handoff de diseño a desarrollo"],
        ["Hotjar","Mapas de calor y grabaciones de sesión"],
    ]),
    callout("Un usuario que no puede usar una funcionalidad, no importa qué tan bien esté implementada, es una funcionalidad fallida.", "🎯"),
]),

# 20
("🔄 Metodologías Ágiles", [
    h1("Metodologías Ágiles"),
    quote("Individuos e interacciones sobre procesos y herramientas. Software funcionando sobre documentación exhaustiva. — Manifiesto Ágil"),
    div(),
    h2("Los 4 valores del Manifiesto Ágil"),
    n("Individuos e interacciones > Procesos y herramientas."),
    n("Software funcionando > Documentación exhaustiva."),
    n("Colaboración con el cliente > Negociación de contratos."),
    n("Respuesta al cambio > Seguimiento de un plan."),
    div(),
    h2("Scrum"),
    h3("Roles"),
    b("Product Owner — dueño del backlog, define prioridades, voz del negocio."),
    b("Scrum Master — facilita el proceso, elimina impedimentos."),
    b("Development Team — equipo auto-organizado que construye el producto."),
    h3("Eventos"),
    table([
        ["Evento","Duración","Propósito"],
        ["Sprint","1-4 semanas","Iteración de desarrollo"],
        ["Sprint Planning","≤ 8h","Seleccionar y planear el sprint"],
        ["Daily Scrum","15 min","Sincronización diaria"],
        ["Sprint Review","≤ 4h","Demo del incremento al stakeholder"],
        ["Retrospectiva","≤ 3h","Mejora continua del equipo"],
    ]),
    div(),
    h2("Kanban"),
    b("Visualizar el flujo de trabajo en un tablero con columnas (Por hacer / En progreso / Hecho)."),
    b("Limitar el WIP (Work in Progress) para detectar cuellos de botella."),
    b("Gestionar el flujo, no las iteraciones. No hay sprints."),
    b("Más adecuado para trabajo operativo y soporte."),
    div(),
    h2("Scrum vs Kanban"),
    table([
        ["Aspecto","Scrum","Kanban"],
        ["Iteraciones","Sprints fijos","Flujo continuo"],
        ["Roles definidos","Sí (PO, SM, Team)","No obligatorios"],
        ["Cambios mid-sprint","No recomendado","En cualquier momento"],
        ["Métricas clave","Velocity, burndown","Lead time, cycle time"],
    ]),
]),

# 21
("📋 Gestión de Proyectos de Software", [
    h1("Gestión de Proyectos de Software"),
    p("Planeación, organización, dirección y control de recursos para alcanzar objetivos de software."),
    div(),
    h2("Triple restricción (Iron Triangle)"),
    b("Alcance — qué funcionalidades incluye el proyecto."),
    b("Tiempo — cuándo se entrega."),
    b("Costo — cuánto cuesta (personas, infraestructura, licencias)."),
    callout("Cambiar una restricción impacta las otras dos. No puedes tener más alcance sin más tiempo o costo.", "⚠️"),
    div(),
    h2("Estimación de esfuerzo"),
    table([
        ["Técnica","Descripción"],
        ["Story Points (Fibonacci)","Estimación relativa de complejidad. 1,2,3,5,8,13,21"],
        ["Planning Poker","El equipo estima en paralelo para evitar sesgos."],
        ["T-shirt sizing","S, M, L, XL para estimaciones rápidas"],
        ["Three-Point (PERT)","(Optimista + 4×Más probable + Pesimista) / 6"],
        ["Análisis de puntos de función","Cuenta entradas, salidas, consultas, archivos"],
    ]),
    div(),
    h2("Gestión de riesgos"),
    n("Identificar riesgos — lluvia de ideas, revisión de lecciones aprendidas."),
    n("Analizar probabilidad e impacto."),
    n("Planear respuesta — mitigar, transferir, aceptar, evitar."),
    n("Monitorear durante todo el proyecto."),
    div(),
    h2("Herramientas de planificación"),
    b("Diagrama de Gantt — cronograma visual de tareas y dependencias."),
    b("WBS (Work Breakdown Structure) — descompone el proyecto en entregables."),
    b("Ruta crítica (CPM) — secuencia de tareas que determina la duración mínima."),
    b("Jira, Trello, Asana, Linear — herramientas de gestión de tareas y proyectos."),
    b("GitHub Projects, GitLab — integración con control de versiones."),
]),

# 22
("✅ Calidad de Software y Testing", [
    h1("Calidad de Software y Testing"),
    p("La calidad del software es la medida en que cumple los requisitos funcionales, de rendimiento y de mantenibilidad."),
    div(),
    h2("Pirámide de pruebas"),
    callout("Más pruebas unitarias (rápidas y baratas) → menos pruebas de integración → pocas pruebas E2E (lentas y costosas).", "🔺"),
    h3("Tipos de prueba"),
    table([
        ["Tipo","Qué prueba","Herramientas"],
        ["Unitarias","Función o clase aislada","Jest, pytest, JUnit"],
        ["Integración","Interacción entre módulos","pytest, Spring Test"],
        ["End-to-End (E2E)","Flujo completo del usuario","Cypress, Playwright, Selenium"],
        ["Performance","Tiempo de respuesta bajo carga","k6, JMeter, Locust"],
        ["Seguridad","Vulnerabilidades y accesos no autorizados","OWASP ZAP, Burp Suite"],
    ]),
    div(),
    h2("Cobertura de código"),
    b("Line coverage — % de líneas ejecutadas por las pruebas."),
    b("Branch coverage — % de ramas condicionales cubiertas."),
    b("Mutation testing — introduce cambios y verifica que las pruebas los detecten."),
    callout("100% de cobertura no garantiza calidad. Prioriza pruebas de lógica de negocio crítica.", "⚠️"),
    div(),
    h2("CI/CD para calidad"),
    n("Pre-commit hooks — linting y formateo antes del commit."),
    n("CI pipeline — ejecuta pruebas automáticamente en cada push."),
    n("Code review obligatorio — al menos un aprobador antes de merge."),
    n("Análisis estático — SonarQube, ESLint, Pylint detectan code smells."),
    n("Feature flags — desplegar código inactivo, activarlo para % de usuarios."),
    div(),
    h2("Métricas de calidad"),
    b("Defect density — número de bugs por KLOC (mil líneas de código)."),
    b("MTTR (Mean Time to Repair) — tiempo promedio en corregir un fallo."),
    b("Deuda técnica — costo estimado de refactorizar código problemático."),
    b("NPS del desarrollador — qué tan fácil es trabajar con el código base."),
    code("""# Ejemplo: prueba unitaria con pytest
def calcular_isr(ingreso):
    if ingreso <= 7000:
        return ingreso * 0.0
    elif ingreso <= 12000:
        return (ingreso - 7000) * 0.06
    return (ingreso - 12000) * 0.16 + 300

def test_ingreso_sin_isr():
    assert calcular_isr(5000) == 0

def test_ingreso_segunda_banda():
    assert calcular_isr(10000) == 180.0

def test_ingreso_tercera_banda():
    assert calcular_isr(15000) == 780.0""", "python"),
]),

]  # fin de PAGINAS

# ── función para crear una página con bloques ─────────────────────────────────

def crear_pagina_rica(parent_id, titulo, bloques):
    # La Notion API acepta máx ~100 bloques por request
    pagina = notion.pages.create(
        parent={"type": "page_id", "page_id": parent_id},
        properties={"title": [{"type": "text", "text": {"content": titulo}}]},
        children=bloques[:100],
    )
    pid = pagina["id"]
    # Si hay más bloques, los appendamos en batches de 100
    rest = bloques[100:]
    while rest:
        notion.blocks.children.append(block_id=pid, children=rest[:100])
        rest = rest[100:]
    return pid, pagina.get("url", "")

# ── ejecutar ──────────────────────────────────────────────────────────────────

def main():
    print(f"Conectado a Notion. Creando base de conocimientos ISC bajo {PARENT[:8]}...")

    # Página índice
    idx_titulo = "📚 ISC — Base de Conocimientos"
    idx_bloques = [
        h1("Base de Conocimientos · Ingeniería en Sistemas Computacionales"),
        callout("Esta base reúne los temas fundamentales del programa de ISC. Creada automáticamente por Athena.", "🤖"),
        p("Navega a cualquier tema usando las sub-páginas de abajo."),
        div(),
        h2("Temas incluidos"),
    ] + [b(titulo) for titulo, _ in PAGINAS]

    idx_id, idx_url = crear_pagina_rica(PARENT, idx_titulo, idx_bloques)
    print(f"✅ Índice creado: {idx_url}")

    # Sub-páginas (hijo del índice)
    for i, (titulo, bloques) in enumerate(PAGINAS, 1):
        try:
            pid, url = crear_pagina_rica(idx_id, titulo, bloques)
            print(f"  [{i:02d}/{len(PAGINAS)}] ✅ {titulo}")
        except Exception as e:
            print(f"  [{i:02d}/{len(PAGINAS)}] ❌ {titulo} — {e}")
        time.sleep(0.35)  # respetar rate limit de Notion (~3 req/s)

    print(f"\n🎉 Listo — {len(PAGINAS) + 1} páginas creadas. Índice: {idx_url}")

if __name__ == "__main__":
    main()
