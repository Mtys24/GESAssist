Especificación de Motor de Reglas: Elegibilidad GES (Garantías Explícitas en Salud) - Chile

Versión del Marco Regulatorio: Decreto Supremo N° 29 (Trienio 2025-2028) - 90 Problemas de Salud.
Público Objetivo: Agentes de IA, Motores de Inferencia (BRMS), Desarrolladores de Software de Salud.

1. Diccionario de Datos (Input Schema)

Para que el agente evalúe un caso, la carga útil (Payload) de entrada debe estructurarse de la siguiente manera:

{
  "paciente": {
    "rut": "string",
    "edad_anios": "integer",
    "edad_meses": "integer",
    "prevision": "ENUM('FONASA', 'ISAPRE', 'CAPREDENA', 'DIPRECA', 'PARTICULAR')"
  },
  "diagnostico": {
    "codigo_minsal_ges": "integer", // Códigos del 1 al 90
    "es_sospecha": "boolean",
    "es_confirmacion": "boolean",
    "fecha_diagnostico": "ISO8601 Date"
  },
  "protocolo": {
    "formulario_constancia_ges_firmado": "boolean",
    "atencion_en_red_cerrada": "boolean", // TRUE si se atiende donde indica Fonasa/Isapre
    "prestacion_solicitada_en_canasta": "boolean"
  },
  "historial_isapre": {
    "condicion_preexistente_declarada": "boolean",
    "es_enfermedad_salud_mental": "boolean" // Relevante para Ley 21.331
  }
}


2. Motor de Reglas Principal (Lógica de Inclusión)

Para que un paciente sea habilitado para activar las garantías GES, la evaluación debe retornar TRUE en la siguiente secuencia de compuertas lógicas (AND).

Pseudocódigo de Validación Base:

def evaluar_elegibilidad_ges(payload):
    # REGLA 1: Tipo de Previsión Válida
    # Exclusión absoluta: Fuerzas Armadas (CAPREDENA/DIPRECA) y Particulares sin previsión.
    if payload.paciente.prevision NOT IN ('FONASA', 'ISAPRE'):
        return RECHAZADO_POR_PREVISION
    
    # REGLA 2: Pertenencia al Decreto Vigente
    # El código debe estar entre los 90 Problemas de Salud vigentes (DS 29).
    if payload.diagnostico.codigo_minsal_ges < 1 OR payload.diagnostico.codigo_minsal_ges > 90:
        return RECHAZADO_PATOLOGIA_NO_GES

    # REGLA 3: Cumplimiento de Criterios Específicos (Ejemplos con códigos reales MINSAL)
    if payload.diagnostico.codigo_minsal_ges == 10: # Escoliosis
        if payload.paciente.edad_anios >= 25:
            return RECHAZADO_POR_EDAD # GES de escoliosis cubre a menores de 25 años
            
    if payload.diagnostico.codigo_minsal_ges == 12: # Artrosis de Cadera
        if payload.paciente.edad_anios < 65:
            if not es_artrosis_secundaria(payload.diagnostico):
                return RECHAZADO_POR_EDAD # GES primario es para 65 y más
                
    # REGLA 4: Formalidad Administrativa (Obligatoria)
    if payload.protocolo.formulario_constancia_ges_firmado == FALSE:
        return PENDIENTE_DE_NOTIFICACION
        
    # REGLA 5: Uso de la Red Prestadora
    if payload.protocolo.atencion_en_red_cerrada == FALSE:
        if no_hay_excepcion_urgencia_vital(payload):
            return RECHAZADO_POR_RED_EXTRACONTRACTUAL

    return ELEGIBLE_ACTIVACION_GES


3. Matriz de Exclusión y Casos Borde

Un paciente con previsión válida y patología GES puede ser excluido o perder la cobertura si cumple alguna de estas condiciones:

A. Exclusiones por Cobertura ("Fuera de Canasta")

Lógica: IF prestacion_solicitada_en_canasta == FALSE THEN Cobertura_GES = FALSE

Razón: El paciente tiene la patología, pero pide un medicamento, insumo o cirugía de una tecnología más cara o diferente a la especificada en el protocolo (Arancel Fonasa/Isapre). Se cubre por CAEC o Plan Complementario, no por GES.

B. Preexistencias en Isapre (Manejo Normativo)

Regla General: Si el paciente omitió declarar una enfermedad preexistente en su Declaración de Salud (DPS) al ingresar a la Isapre, la Isapre PUEDE NEGAR la cobertura GES para esa enfermedad específica.

Excepción Legal (Salud Mental - Ley 21.331): Las Isapres no pueden exigir declaración de enfermedades y condiciones de salud mental como preexistencias. Por tanto:

IF historial.condicion_preexistente == TRUE AND historial.es_enfermedad_salud_mental == TRUE THEN Excluir_Cobertura = FALSE (El paciente SÍ tiene derecho a GES).

4. Máquina de Estados: Suspensión y Cierre de Casos

Una vez que el paciente está habilitado, el caso entra en estado ACTIVO. Existen reglas estrictas para transicionar al estado CERRADO o SUSPENDIDO.

Reglas de Cierre por Inasistencia (Superintendencia de Salud)

Un prestador de la red puede cerrar el caso GES (perdiendo el paciente la garantía de oportunidad temporal) si:

Inasistencias Consecutivas: El paciente falta a 2 citaciones médicas consecutivas sin justificación.

Inasistencias Discontinuas: El paciente falta a 3 citaciones médicas discontinuas durante el ciclo de tratamiento sin justificación.

Acción del Agente: IF inasistencias_consecutivas == 2 OR inasistencias_totales == 3 THEN Estado = CERRADO_POR_INASISTENCIA.

Reglas de Cierre Clínico / Administrativo

Alta Médica Integral: El médico determina la resolución del problema de salud.

Fallecimiento: Terminación automática de la póliza/garantía.

Renuncia Expresa: El paciente firma un documento formal renunciando al prestador designado para tratarse por la modalidad de libre elección.

Fuerza Mayor Médica: Una patología intercurrente más grave impide el tratamiento GES actual (Ej. Paciente con GES de Cataratas sufre un Infarto agudo. Se suspende Cataratas, se activa Infarto).

5. Excepciones de Protección al Paciente (Lógica de Reclamo)

Falta de Notificación:
Si un paciente fue diagnosticado con una patología GES (ej. VIH - Código 18) pero el médico omitió entregar y hacer firmar el Formulario de Constancia GES:

Lógica del Agente: El reloj del tiempo máximo de espera (Garantía de Oportunidad) no ha comenzado a correr legalmente, pero el paciente NO PIERDE su derecho. El agente debe dictaminar: Habilitar_Retroactivamente = TRUE e instruir al prestador a generar el formulario con fecha de diagnóstico original para obligar al cumplimiento.