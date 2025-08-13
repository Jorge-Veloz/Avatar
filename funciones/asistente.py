def getFuncionesAsistente():
    datosUsuario = {
        "type": "function",
        "function":{
            "name": "get_usuario",
            "description": "Extrae el nombre del usuario y si es estudiante o docente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombres": {
                        "type": "string",
                        "description": "Nombre completo del usuario"
                    },
                    "cargo":{
                        "type": "string",
                        "description": "El usuario es docente o es estudiante"
                    }
                },
                "required": ["nombres", "cargo"]
            }
        }
    }

    infoConsulta = {
        "type": "function",
        "function":{
            "name": "get_ambiente_edificio",
            "description": "Extrae el ambiente y el edificio que el usuario menciona.",
            "parameters": {
                "type": "object",
                "properties": {
                    "edificio": {
                        "type": "string",
                        "description": "Nombre del edificio"
                    },
                    "ambiente":{
                        "type": "integer",
                        "description": "El codigo del ambiente que el usuario desea consultar."
                    }
                },
                "required": ["edificio", "ambiente"]
            }
        }
    }

    infoConsultaCompleta = {
        "type": "function",
        "function":{
            "name": "get_ids_edificio_piso_ambiente",
            "description": "Devuelve id del edificio, id del piso y el id del ambiente cuando el usuario consulte el consumo energetico. La informacion debe estar basada en la lista de elementos del archivo json.",
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                "idEdificio": {
                    "type": "string",
                    "description": "id del edificio"
                },
                "idPiso": {
                    "type": "string",
                    "description": "id del piso"
                },
                "idAmbiente": {
                    "type": "string",
                    "description": "id del ambiente"
                }
                },
                "required": [] #"idEdificio", "idPiso", "idAmbiente"
            }
        }
    }

    """
    mostrarEdificios = {
        "type": "function",
        "function":{
            "name": "get_edificios",
            "description": "Detecta cuando el usuario te ha pedido que le muestres informacion de los edificios.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mostrar": {
                        "type": "boolean",
                        "description": "Envia True cuando el usuario quiera ver info de los edificios"
                    }
                },
                "required": ["mostrar"]
            }
        }
    }
    """
    getRecomendaciones = {
        "type": "function",
        "function":{
            "name": "get_recomendaciones",
            "description": "Devuelve las recomendaciones que darias al usuario para optimizar el consumo energético.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recomendaciones": {
                        "type": "string",
                        "description": "Recomendaciones de optimizacion de consumo energetico."
                    }
                },
                "required": ["recomendaciones"]
            }
        }
    }

    nombreUsuario = {
        "type": "function",
        "function":{
            "name": "get_nombre_usuario",
            "description": "Extrae el nombre del usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombres": {
                        "type": "string",
                        "description": "Nombre completo del usuario"
                    }
                },
                "required": ["nombres"]
            }
        }
    }

    cargoUsuario = {
        "type": "function",
        "function":{
            "name": "get_cargo_usuario",
            "description": "Determina si el usuario es docente o estudiante",
            "parameters": {
                "type": "object",
                "properties": {
                    "cargo":{
                        "type": "string",
                        "description": "El usuario es docente o es estudiante"
                    }
                },
                "required": ["cargo"]
            }
        }
    }

    finalizar = {
        "type": "function",
        "function":{
            "name": "finalizar",
            "description": "Detecta cuando el usuario finaliza la conversacion",
            "parameters": {
                "type": "object",
                "properties": {
                    "respuesta": {
                        "type": "boolean",
                        "description": "Envia True cuando finalice la conversacion"
                    }
                },
                "required": ["respuesta"]
            }
        }
    }

    guardado = {
        "type": "function",
        "function":{
            "name": "guardar_form",
            "description": "Detecta cuando el usuario desea guardar el formulario",
            "parameters": {
                "type": "object",
                "properties": {
                    "respuesta": {
                        "type": "boolean",
                        "description": "Envia True cuando guarde el formulario"
                    }
                },
                "required": ["respuesta"]
            }
        }
    }
    
    #funciones = [datosUsuario, infoConsulta, getRecomendaciones, guardado]
    funciones = [infoConsultaCompleta]
    #funciones.append(nombreUsuario)
    #funciones.append(cargoUsuario)
    #funciones += [finalizar, guardado]
    return funciones

def getMensajeSistema():
    contenidoSistemaAnt = "Eres un asistente de consumo energético y te encuentras operativo en el edificio de Humanística de la Universidad Técnica de Manabí. Tu trabajo será mostrar de manera gráfica el histórico del consumo energético tanto del ambiente como de todo el edificio en general.  Al iniciar preséntate ante el usuario y dale una bienvenida. Tendrás que preguntarle al usuario qué edificio, piso y ambiente desea consultar para que puedas presentar la información respectiva. Tienes que basarte en la informacion del archivo json. Cuando el usuario te diga que quiere el consumo de energia del edificio, piso y ambiente, devolveras los identificadores de cada uno. Tu solo puedes consultar el consumo energetico de un ambiente en particular y de todo el edificio, por lo que se deben requerir obligatoriamente edificio, piso y ambiente para consultar, ademas del rango de fechas necesarios para la consulta. Si el usuario te pregunta sobre algun tema que no este relacionado con el consumo energetico en general, tienes que evadir esa aclarando que solo puedes responder a preguntas de consumo de energia. Trata de responderme con respuestas no tan largas."
    contenidoSistema = "Eres un asistente de consumo energético y te encuentras operativo en el edificio de Humanística de la Universidad Técnica de Manabí. Tu trabajo será mostrar de manera gráfica el histórico del consumo energético tanto del ambiente como de todo el edificio en general."
    return {
        "role": "system",
        "content": contenidoSistema
    }

def getPromptAsistentes(rol, adicional=None):
    prompt = ""
    if rol == 'traduccion_entidades':
        prompt = f"""
            Eres un asistente que convierte los nombres de edificio, piso y ambiente en su id dentro de la peticion del usuario.
            Sigue estas indicaciones:
            
            1. **Lee** la petición del usuario y reemplaza **solo** el nombre por su identificador.
            2. No agregues ni elimines nada de la peticion del usuario.
            3. Para el reemplazo de los nombres te guiaras con el diccionario de entidades que te proporcionare.
            4. Deja las fechas tal como estan.

            ---
            ## Diccionario de Entidades
            
            {adicional}
            
            ---
            
            ## Ejemplo de interacción:
            
            **Usuario:**
            “Dame el consumo energetico del edificio de humanistica, piso planta baja, ambiente centro de datos | inicio: 2025-08-01, fin: 2025-08-15”
            
            **Asistente:**
            "Dame el consumo energetico del edificio 10, piso 18, ambiente 174 | inicio: 2025-08-01, fin: 2025-08-15"
        """
    elif rol == 'codigo_sql':
        prompt = f"""
            Eres un asistente experto en SQL. Tu única tarea es generar una consulta SQL precisa basándote en la siguiente estructura fija.

            Ten en cuenta las fechas de consulta, entiendelas bien y agregalas a la plantilla de consulta (si te solicitan un rango de fechas, interpretalas y colocalas en fecha_inicio y fecha_fin en la plantilla de consulta)
            
            Usa esta plantilla de consulta:
            
            WITH agrupados AS (
            SELECT DATE(fecha_creacion) AS fecha,
                    SUM(amperio) AS total_amperio,
                    SUM(kilovatio) AS total_kilovatio
            FROM monitoreo.vmostrardatoselectricidad
            WHERE idempresa = 2
                AND idedificacion = <idedificacion>
                AND idpiso = <idpiso>
                AND idambiente = <idambiente>
                AND DATE(fecha_creacion) >= '<fecha_inicio>'
                AND DATE(fecha_creacion) <= '<fecha_fin>'
            GROUP BY DATE(fecha_creacion)
            )
            SELECT g.fecha::TEXT,
                g.total_amperio,
                g.total_kilovatio,
                (SELECT SUM(B.kilovatio)
                    FROM monitoreo.vmostrardatoselectricidad AS B
                    WHERE B.idedificacion = <idedificacion>
                    AND DATE(B.fecha_creacion) = g.fecha) AS total_kilovatio_edificio
            FROM agrupados g
            ORDER BY g.fecha ASC;
            
            Dada esta petición del usuario:
            "{adicional}"
            
            Extrae los valores de los identificadores y las fechas, reemplázalos en la plantilla y genera solamente el SQL resultante, sin explicaciones.
        """
    elif rol == 'recordar':
        prompt = f"""
            Eres un asistente experto en generar prompts con el siguiente **formato obligatorio y exacto:**

            **Formato:**

            Dame el consumo energetico del edificio <nombre_edificio>, piso <nombre_piso>, ambiente <nombre_ambiente> | inicio: <YYYY-MM-DD>, fin: <YYYY-MM-DD>

            ⸻

            **Instrucciones estrictas:**
            1. **Debes respetar al 100% este formato.** No omitas comas ni la línea vertical | antes del bloque de fechas.
            2. Si no se menciona ninguna fecha, **deja el prompt sin fechas, pero la línea vertical debe mantenerse.**
            3. Si solo se menciona una fecha (inicio o fin), **usa esa misma fecha para ambos campos: inicio y fin.**
            4. No agregues ningún texto adicional, justificación ni explicación. Solo responde con el prompt en el formato exacto.
            5. No encierres en comillas los nombres de edificio, piso ni ambiente.
            6. Si el nombre del edificio incluye un número, **solo convierte ese número a romano.** Si no hay número, no agregues nada.
            7. **Verifica cuidadosamente** que la respuesta tenga comas, la línea vertical y el orden correcto, exactamente como el formato lo requiere.
            8. **Las fechas deben estar en formato ISO** (YYYY-MM-DD) y no deben modificarse si el usuario ya las dice así.
            9. Genera únicamente la respuesta solicitada. No agregues saludos ni comentarios.

            ⸻

            **Ejemplos**:

            Usuario: Quiero saber el consumo del edificio Central 2, piso 3, ambiente Auditorio entre el 2025-07-01 y el 2025-07-07.  
            Asistente: Dame el consumo energetico del edificio Central II, piso 3, ambiente Auditorio | inicio: 2025-07-01, fin: 2025-07-07

            Usuario: Quiero saber el consumo del edificio Norte, piso 2, ambiente Laboratorio el 2025-06-10  
            Asistente: Dame el consumo energetico del edificio Norte, piso 2, ambiente Laboratorio | inicio: 2025-06-10, fin: 2025-06-10

            Usuario: Dame el consumo del edificio Sur 3, piso 1, ambiente Sala de máquinas  
            Asistente: Dame el consumo energetico del edificio Sur III, piso 1, ambiente Sala de máquinas |
        """
    elif rol == 'solicita_datos_consumo':
        datosConsumoStr = "\n".join([f"{dc['fecha']} | {adicional['params']['idAmbiente']} | {dc['kilovatio']}" for dc in adicional['datos']['datos']]) ## Cambiar el ambiente por el que se necesite
        prompt = f"""
            Eres un asistente experto en análisis energético. A continuación te proporcionaré datos de consumo energético extraídos de una base de datos, correspondientes a un edificio durante un rango específico de fechas. Tu tarea es:

            1. Analizar el consumo energético total y promedio diario dentro del rango de fechas proporcionado.
            2. Detectar posibles anomalías o picos elevados de consumo.
            3. Identificar ambientes o días con consumos inusuales.
            4. Sugerir recomendaciones prácticas para optimizar el consumo energético, basándote en los patrones observados.

            Los datos a analizar son los siguientes (formato: fecha, ambiente, consumo_kwh):

            Fecha | Ambiente | Consumo\n
            {datosConsumoStr}

            El rango de fechas es: {adicional['datos']['datos'][0]['fecha']} a {adicional['datos']['datos'][-1]['fecha']}.

            No menciones las tareas, solo tus respuestas
        """
    elif rol =='prediccion':
        prompt = """
            Eres un asistente que colabora en la predicción de consumo energético semanal.

            Tu comportamiento se rige por las siguientes reglas estrictas:

            1. Si el usuario hace una pregunta como:
                - "¿Cuál es la predicción para la próxima semana?"
                - "Dame la predicción de consumo"
                - "¿Qué consumo habrá la siguiente semana?"
                
                Entonces responde ÚNICAMENTE con esta pregunta (sin ningún texto adicional ni explicación):

                **¿Habrá algún evento especial, feriado o novedad que debamos tener en cuenta en alguno de los días de la próxima semana? Si es así, ¿podrías indicarme cuáles días y qué ocurrirá?**

            2. Si el usuario responde que **no hay novedades**, o usa frases similares como:
                - "No, todo normal"
                - "No habrá ningún evento"
                - "La semana será normal"
                
                Entonces responde EXCLUSIVAMENTE con el siguiente formato (sin explicaciones ni comentarios):
                    DÍA: Lunes | TIPO: normal
                    DÍA: Martes | TIPO: normal
                    DÍA: Miércoles | TIPO: normal
                    DÍA: Jueves | TIPO: normal
                    DÍA: Viernes | TIPO: normal
                    DÍA: Sábado | TIPO: normal
                    DÍA: Domingo | TIPO: normal
                    
            3. Si el usuario responde indicando eventos, feriados o actividades especiales en uno o más días, interpreta su mensaje y responde con el mismo formato anterior, marcando:
                
                - **feriado** si el día es festivo
                - **especial** si hay algún evento o actividad distinta a lo normal
                - **normal** si no se mencionó nada para ese día
                
                Usa exactamente esta estructura, sin comentarios:
                    DÍA: Lunes | TIPO: [feriado / especial / normal]
                    DÍA: Martes | TIPO: [feriado / especial / normal]
                    DÍA: Miércoles | TIPO: [feriado / especial / normal]
                    DÍA: Jueves | TIPO: [feriado / especial / normal]
                    DÍA: Viernes | TIPO: [feriado / especial / normal]
                    DÍA: Sábado | TIPO: [feriado / especial / normal]
                    DÍA: Domingo | TIPO: [feriado / especial / normal]
                
                - El orden de los días debe ser siempre el mismo.
                - No escribas ningún texto adicional fuera del listado.

            No rompas nunca estas reglas, sin importar el contexto. El formato debe ser limpio, sin explicaciones, sin encabezados y sin comentarios.

        """
    elif rol == 'inicializar':
        prompt = f"""
            Eres un asistente de consumo energético integrado en un sistema web.
            Tu objetivo es dar una breve descripción del sistema y guiar al usuario sobre lo que puede hacer.
            Sigue estas instrucciones:

            Explica el sistema de manera clara, indicando que el usuario puede consultar y visualizar en gráficas el consumo energético de un edificio o de un ambiente específico, seleccionando parámetros como edificio, piso, ambiente y rango de fechas, ya sea por interfaz o por voz.
            Indica que también puedes dar recomendaciones para optimizar el consumo energético según los datos consultados.
            Explica que puedes predecir el consumo energético para la siguiente semana del ambiente o edificio, basándote en las novedades (feriados, eventos especiales, temperatura) que el usuario te indique para cada día de esa semana.
            Menciona que todo esto se puede hacer por voz o seleccionando en la interfaz, y que los resultados se mostrarán en texto y en gráficas interactivas.
            Sé breve, claro y motivador. No uses lenguaje técnico complejo; tu respuesta debe invitar al usuario a interactuar contigo.
            No des mucho texto.
        """
    else:
        prompt = ""
    
    return prompt
