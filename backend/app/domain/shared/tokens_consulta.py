import re


class TokensConsulta:
    """Servicio de dominio: extrae tokens significativos de una consulta conversacional.

    La consulta entra ya normalizada (sin tildes, minusculas). Tokenizamos por
    secuencias alfanumericas para ignorar signos de puntuacion y luego filtramos
    stopwords conversacionales que nunca deberian pasar al full-text del catalogo.
    El objetivo: si el cliente escribe en frases naturales tipo
    'quiero, muestrame algo bueno', el query que llega al catalogo queda vacio."""

    _RX_TOKEN = re.compile(r"[a-z]+|\d+")

    STOPWORDS = frozenset({
        "el", "la", "los", "las", "un", "una", "unos", "unas", "del", "al",
        "lo", "le", "les", "se", "me", "te", "nos",
        "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
        "aquel", "aquella", "aquellos", "aquellas",
        "yo", "vos", "usted", "ustedes", "nosotros", "ellos", "ellas",
        "mi", "mis", "tus", "su", "sus", "nuestro", "nuestra", "nuestros", "nuestras",

        "de", "en", "con", "sin", "por", "para", "segun", "hasta", "desde",
        "entre", "sobre", "bajo", "ante", "tras", "contra", "hacia", "mediante",
        "y", "o", "u", "ni", "pero", "mas", "sino", "aunque", "si", "que",
        "como", "porque", "porq", "pq", "pues", "cuando", "donde", "mientras",
        "entonces", "asi", "tambien", "tampoco", "ademas", "aun",

        "cual", "cuales", "quien", "quienes", "cuanto", "cuanta", "cuantos",
        "cuantas", "adonde",

        "querer", "quiero", "quieres", "queres", "quiere", "queremos", "quieren",
        "queria", "querias", "querian", "queriamos",
        "querria", "querrias", "querrian", "querriamos",
        "quisiera", "quisieras", "quisieramos", "quisieran",
        "quise", "quisiste", "quiso", "quisimos", "quisieron",
        "quiera", "quieras", "quieran", "queriendo",

        "necesitar", "necesito", "necesitas", "necesita", "necesitamos",
        "necesitan", "necesitaba", "necesitabas", "necesitaban",
        "necesitaria", "necesitarias", "necesitarian",
        "necesite", "necesites", "necesiten", "necesitare", "necesitando",

        "buscar", "busco", "buscas", "busca", "buscamos", "buscan",
        "buscaba", "buscaban", "buscaria", "buscarian", "buscare",
        "busque", "busques", "busquen", "buscando",

        "desear", "deseo", "deseas", "desea", "deseamos", "desean",
        "deseaba", "desearia", "desee", "desees", "deseen",

        "pedir", "pido", "pides", "pide", "pedimos", "piden",
        "pedia", "pediria", "pedire", "pida", "pidas", "pidan", "pidiendo",

        "tener", "tengo", "tienes", "tenes", "tiene", "tenemos", "tienen",
        "tenia", "tenias", "tenian", "teniamos",
        "tendria", "tendrias", "tendrian", "tendre", "tendremos",
        "tenga", "tengas", "tengan", "teniendo", "tenido", "tenida",
        "tuviera", "tuvieras", "tuvieran", "tuve", "tuviste", "tuvo", "tuvimos",

        "ir", "voy", "vas", "va", "vamos", "van", "iba", "ibas", "iban",
        "iria", "irias", "irian", "vaya", "vayas", "vayan", "ido", "ida",

        "hacer", "hago", "haces", "haces", "hace", "hacemos", "hacen",
        "hacia", "hacian", "haria", "harias", "harian",
        "haga", "hagas", "hagan", "haciendo", "hecho", "hecha",

        "poder", "puedo", "puedes", "podes", "puede", "podemos", "pueden",
        "podia", "podias", "podian", "podria", "podrias", "podrian",
        "pueda", "puedas", "puedan", "pudiera", "pudieras", "pudieran",

        "gustar", "gusta", "gustan", "gusto", "gustaria", "gustarias",
        "gustarian", "guste", "gustes", "gusten",

        "agradar", "agrada", "agradan", "agradaria", "agradaria",
        "encanta", "encantan", "encantaria", "fascina", "fascinan",

        "interesar", "interesa", "interesan", "interese", "intereses",
        "interesen", "interesaba", "interesaria", "interesado", "interesada",

        "preferir", "prefiero", "prefieres", "preferes", "prefiere",
        "preferimos", "prefieren", "preferia", "preferias", "preferian",
        "preferiria", "prefiera", "prefieras", "prefieran", "preferido",

        "importar", "importa", "importan", "importe", "importen",
        "importaba", "importaria",

        "mostrar", "muestra", "muestras", "muestre", "muestren",
        "mostrame", "mostranos", "muestreme", "muestrenme", "muestrame",
        "muestranos", "mostrarme", "mostrarnos", "mostrarte", "mostrado",
        "mostramos",

        "ensenar", "ensena", "ensenas", "ensenan", "ensename", "ensenenme",
        "ensenarme", "ensenado",

        "dar", "dame", "damos", "dan", "das", "doy", "demela", "demelas",
        "damelo", "damela", "damelos", "damelas", "den", "des", "de",
        "dara", "daran", "daria", "darias", "darian", "darme", "darte",
        "dado", "dada",

        "ver", "vea", "veamos", "ve", "ven", "veo", "ves", "vere",
        "veras", "veremos", "veran", "veria", "verias", "verian",
        "verlo", "verla", "verlos", "verlas", "viendo", "visto", "vista",

        "ofrecer", "ofrece", "ofrecen", "ofreces", "ofrezcame", "ofrezca",
        "ofrecia", "ofreceria", "ofrezcame", "ofrecido",

        "recomendar", "recomienda", "recomiendas", "recomiendes",
        "recomiendan", "recomienden", "recomiendame", "recomiendenme",
        "recomendarme", "recomendame", "recomendaba", "recomendaria",
        "recomendado", "recomendacion", "recomendaciones",

        "aconsejar", "aconseja", "aconsejas", "aconsejen", "aconsejame",
        "aconsejarme", "aconsejaria", "aconsejaras", "aconsejenme",
        "consejo", "consejos",

        "asesorar", "asesora", "asesoras", "asesores", "asesoren",
        "asesorame", "asesorarme", "asesorenme", "asesoria", "asesoramiento",
        "asesor",

        "sugerir", "sugiere", "sugieras", "sugieran", "sugiereme",
        "sugerencia", "sugerencias", "sugiera", "sugiero", "sugieren",
        "sugiriera", "sugerido",

        "ayudar", "ayuda", "ayudame", "ayudas", "ayuden", "ayudaria",
        "ayudenme", "ayudanos", "ayudandome", "ayudando", "ayudado",

        "decir", "dice", "decime", "digo", "dices", "dicen", "diga",
        "digas", "digan", "dire", "diras", "diria", "dirias", "dicho",
        "dicha", "decime", "dime", "digame",

        "saber", "sabe", "sabes", "saben", "sepa", "sepas", "sepan",
        "sabias", "sabria", "sabrias", "sabido", "sabiendo",

        "comprar", "compro", "compras", "compre", "compran", "compraba",
        "compraria", "comprado", "comprando", "comprarlo", "comprarla",
        "compremos", "compren",

        "llevar", "llevo", "llevas", "lleva", "llevan", "llevaba",
        "llevaria", "lleve", "lleves", "lleven", "llevarlo", "llevarla",

        "pagar", "pago", "pagas", "paga", "pagan", "pagando", "pagare",
        "pagaria", "pague", "pagues", "paguen", "pagado",

        "usar", "uso", "usas", "usa", "usamos", "usan", "usaba", "usaria",
        "use", "uses", "usen", "usando", "usado", "usada", "usados", "usadas",
        "utilizar", "utilizo", "utiliza", "utilizan", "utilizando",
        "util", "utiles", "utilidad",

        "servir", "sirve", "sirven", "sirvo", "sirves", "servia", "serviria",
        "sirva", "sirvas", "sirvan", "servido",

        "saludar", "saludame",
        "bueno", "buenos", "buena", "buenas", "mejor", "mejores",
        "excelente", "excelentes", "excelso", "fantastico", "fantastica",
        "malo", "mala", "malos", "malas", "peor", "peores", "pesimo", "pesima",
        "conveniente", "convenientes", "conviene", "convienen", "conviniente",
        "convienen", "conveniencia",
        "recomendable", "recomendables", "aceptable", "aceptables",
        "ideal", "ideales", "optimo", "optima", "optimos", "optimas",
        "perfecto", "perfecta", "perfectos", "perfectas",
        "barato", "barata", "baratos", "baratas",
        "caro", "cara", "caros", "caras",
        "economico", "economica", "economicos", "economicas",
        "accesible", "accesibles", "costoso", "costosa", "costosos", "costosas",
        "lindo", "linda", "lindos", "lindas", "bonito", "bonita",
        "bonitos", "bonitas", "hermoso", "hermosa", "hermosos", "hermosas",
        "chevere", "bacan", "bacano", "piola", "genial", "geniales",
        "copado", "copada", "potente", "potentes",

        "mucho", "mucha", "muchos", "muchas", "poco", "poca", "pocos", "pocas",
        "algo", "nada", "alguno", "alguna", "algun", "algunos", "algunas",
        "ninguno", "ninguna", "ningun", "ningunos", "ningunas",
        "tan", "tanto", "tanta", "tantos", "tantas",
        "bastante", "bastantes", "demasiado", "demasiada", "demasiados",
        "demasiadas", "suficiente", "suficientes",
        "harto", "harta", "hartos", "hartas", "muy", "solo", "solamente",
        "todo", "toda", "todos", "todas",
        "cualquier", "cualquiera", "cualquieras",

        "ahora", "ahorita", "ya", "luego", "despues", "antes", "pronto",
        "nunca", "siempre", "veces", "vez", "rato", "hoy", "ayer", "manana",
        "actualmente", "actualidad", "actual",

        "hola", "holis", "buenas", "saludos",
        "tal", "chau", "chao", "adios", "bye", "dias", "tardes", "noches",
        "gracias", "favor", "porfa", "porfis", "porfavor", "please", "plis",
        "disculpa", "disculpas", "disculpe", "disculpen", "perdon", "perdona",
        "perdone", "perdonen", "claro", "vale", "dale", "listo", "lista",
        "ok", "okey", "okay", "oki", "bien", "exacto", "exacta", "exactos",
        "correcto", "correcta",
        "uff", "uy", "oh", "wow", "mmm", "ah", "eh", "eeh", "mmmh", "ups",
        "oye", "mira", "escucha",

        "pre", "presu", "presupuesto", "presupuestos", "supuesto",
        "precio", "precios", "valor", "valores",
        "costo", "costos", "coste", "costes", "gasto", "gastos",
        "invertir", "inversion", "gastar", "gastamos", "gastando",
        "plata", "platita", "lana", "dinero", "dineros", "efectivo",
        "capital", "recursos", "moneda", "monedas",
        "bolivianos", "boliviano", "bolis", "bob", "bs",
        "dolares", "dolar", "usd", "euro", "euros", "eur",

        "marca", "marcas", "modelo", "modelos", "linea", "lineas", "serie",
        "series", "tipo", "tipos", "clase", "clases", "variedad", "variedades",
        "categoria", "categorias", "subcategoria", "subcategorias",

        "pulgada", "pulgadas", "pulg", "in", "inches",
        "cm", "centimetro", "centimetros", "mt", "mts", "metro", "metros",
        "grande", "grandes", "pequeno", "pequena", "pequenos", "pequenas",
        "mediano", "mediana", "medianos", "medianas", "enorme", "enormes",
        "chico", "chica", "chicos", "chicas", "chiquito", "chiquita",
        "amplio", "amplia", "amplios", "amplias", "espacioso", "espaciosa",
        "tamano", "tamanos",

        "disponible", "disponibles", "disponibilidad",
        "opciones", "opcion", "alternativa", "alternativas",
        "catalogo", "catalogos", "stock", "inventario", "inventarios",
        "hay", "existe", "existen", "esta", "estan",
        "aqui", "alli", "ahi", "alla", "acca",

        "favor", "ayuda", "ayudita", "ayudarme", "ayudenme",

        "hombre", "mujer", "senor", "senora", "senorita", "caballero",
        "dama", "amigo", "amiga", "amigos", "amigas", "cliente", "clientes",
        "persona", "personas", "gente",

        "para mi", "para ti", "para el", "para ella",
    })
    MIN_LEN = 3
    MIN_LEN_NUMERICO = 2

    @classmethod
    def significativos(cls, texto_normalizado: str) -> list[str]:
        if not texto_normalizado:
            return []
        crudo = cls._RX_TOKEN.findall(texto_normalizado)
        return [t for t in crudo if cls._es_significativo(t)]

    @classmethod
    def _es_significativo(cls, t: str) -> bool:
        if t in cls.STOPWORDS:
            return False
        if t.isdigit():
            return len(t) >= cls.MIN_LEN_NUMERICO
        return len(t) >= cls.MIN_LEN

    @classmethod
    def hay_terminos(cls, texto_normalizado: str) -> bool:
        return bool(cls.significativos(texto_normalizado))
