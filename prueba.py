#from modelos.asistente import AsistenteModelo
#import time\
import os

from openai import OpenAI
client = OpenAI(
  api_key=""
)

# Create a vector store caled "Financial Statements"
vector_store = client.vector_stores.create(name="Catalogo edificios pisos y ambientes")

# Ready the files for upload to OpenAI
file_paths = ["objeto.json"]
file_streams = [open(path, "rb") for path in file_paths]

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

# Create an assistant using the file ID
assistant = client.beta.assistants.create(
    instructions="Eres un asistente de consumo energético y te encuentras operativo en el edificio de Humanística de la Universidad Técnica de Manabí. Tu trabajo será mostrar de manera gráfica el histórico del consumo energético tanto del ambiente como de todo el edificio en general. Tendrás que preguntarle al usuario qué edificio, piso y ambiente desea consultar para que puedas presentar la información respectiva. Tienes que basarte en la informacion del archivo json. Cuando el usuario te diga que quiere el consumo de energia del edificio, piso y ambiente, devolveras los identificadores de cada uno.",
    #Eres un asistente de consumo energético y te encuentras operativo en el edificio de Humanística de la Universidad Técnica de Manabí. Tu trabajo será mostrar de manera gráfica el histórico del consumo energético tanto del ambiente como de todo el edificio en general. Tendrás que preguntarle al usuario qué edificio, piso y ambiente desea consultar para que puedas presentar la información respectiva. Tienes que basarte en la informacion del archivo json. Cuando el usuario te diga que quiere el consumo de energia del edificio, piso y ambiente, devolveras los identificadores de cada uno.
    model="gpt-4o",
    tools=[
        {"type": "file_search"},
        {
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
                    "required": [
                    "idEdificio",
                    "idPiso",
                    "idAmbiente"
                    ]
                }
            }
        }
    ],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# message_file = client.files.create(
#   file=open("objeto.json", "rb"), purpose="assistants"
# )

# assistant = client.beta.assistants.update(
#   assistant_id=assistant.id,
#   tool_resources={
#     "code_interpreter": {
#       "file_ids": [message_file.id]
#     }
#   }
# )

thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      #"content": "Dame el consumo energetico del edificio de humanistica, planta baja y ambiente oficina 6",
      "content": "Que pisos tiene el edificio de humanistica?",
    }
  ]
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

#messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
 
print (run)

if run.required_action:
  print("Tool calls:")
  print(run.required_action.submit_tool_outputs.tool_calls)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

if messages and len(messages) > 0:
  print("Contenido mensaje:")
  print(messages)
  message_content = messages[0].content[0].text
  print(message_content.value)
# Define the list to store tool outputs
# tool_outputs = []
 
# # Loop through each tool in the required action section
# for tool in run.required_action.submit_tool_outputs.tool_calls:
#   if tool.function.name == "get_ids_edificio_piso_ambiente":
#     tool_outputs.append({
#       "tool_call_id": tool.id,
#       "success": True
#     })
 
# # Submit all tool outputs at once after collecting them in a list
# if tool_outputs:
#   try:
#     run = client.beta.threads.runs.submit_tool_outputs_and_poll(
#       thread_id=thread.id,
#       run_id=run.id,
#       tool_outputs=tool_outputs
#     )
#     print("Tool outputs submitted successfully.")
#   except Exception as e:
#     print("Failed to submit tool outputs:", e)
# else:
#   print("No tool outputs to submit.")
 
# if run.status == 'completed':
#   messages = client.beta.threads.messages.list(
#     thread_id=thread.id
#   )
#   print(messages)
# else:
#   print(run.status)