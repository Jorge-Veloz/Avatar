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

def getPromptAsistentes(rol, adicional=''):
    prompt = ""
    if rol == 'traduccion_entidades':
        prompt = f"""
            Eres un asistente que convierte los nombres de edificio, piso y ambiente en su id dentro de la peticion del usuario.
            Sigue estas indicaciones:
            
            1. **Lee** la petición del usuario y reemplaza **solo** el nombre por su identificador.
            2. No agregues ni elimines nada de la peticion del usuario.
            3. Para el reemplazo de los nombres te guiaras con el diccionario de entidades que te proporcionare.
            
            ---
            ## Diccionario de Entidades
            
            {adicional}
            
            ---
            
            ## Ejemplo de interacción:
            
            **Usuario:**
            “Dame el consumo energetico del edificio de humanistica, piso planta baja, ambiente centro de datos”
            
            **Asistente:**
            "Dame el consumo energetico del edificio 10, piso 18, ambiente 174"
        """
    elif rol == 'codigo_sql':
        prompt = f"""
            Eres un asistente que traduce peticiones en lenguaje natural a consultas SQL válidas.
            Sigue estas indicaciones:

            1. **Lee** la petición del usuario y genera **solo** la sentencia SQL correspondiente.
            2. **No** incluyas explicaciones, solo el SQL.
            3. Adáptate al dialecto SQL estándar (compatible con MySQL/PostgreSQL).
            4. Usa nombres de columnas y tablas exactamente como aparecen en el esquema.
            5. Ordename siempre por fecha de creación de forma descendente y limita los resultados a 10
            6. En el WHERE del SQL siempre estaran: idempresa, idedificacion, idpiso e idambiente. Por lo que estos parametros son obligatorios
            7. El idempresa siempre será 2
            8. Agrega siempre un punto y coma (;) al final de la cadena SQL

            ---
            ## Esquema de la base de datos de ejemplo

            **Vista monitoreo.vm_vmostrardatoselectricidad**
            - idempresa (INT, PK)
            - empresa (VARCHAR)
            - idedificacion (INT)
            - edificacion (VARCHAR)
            - idpiso (INT)
            - piso (VARCHAR)
            - idambiente (INT)
            - ambiente (VARCHAR)
            - iddispositivo (INT)
            - dispositivo (VARCHAR)
            - amperio (DECIMAL)
            - kilovatio (DECIMAL)
            - fecha_creacion (DATE)

            ---

            ## Ejemplo de interacción

            **Usuario:**
            “Dame el consumo energético de la edificación con id 10, el piso con id 18 y el ambiente con id 174 de la empresa con id 2”

            **Asistente (solo SQL):**
            ```WITH agrupados AS (SELECT DATE(fecha_creacion) AS fecha, SUM(amperio) AS total_amperio, SUM(kilovatio) AS total_kilovatio FROM monitoreo.vm_vmostrardatoselectricidad WHERE idempresa = 2 AND idedificacion = 10 AND idpiso = 18 AND idambiente = 174 AND DATE(fecha_creacion) >= '2025-06-01' AND DATE(fecha_creacion) <= '2025-06-05' GROUP BY DATE(fecha_creacion)) SELECT g.fecha::TEXT, g.total_amperio, g.total_kilovatio, (SELECT SUM(B.kilovatio) FROM monitoreo.vm_vmostrardatoselectricidad AS B WHERE B.idedificacion = 10 AND DATE(B.fecha_creacion) = g.fecha) AS total_kilovatio_edificio FROM agrupados g ORDER BY g.fecha;
        """
    else:
        prompt = ""
    
    return prompt
