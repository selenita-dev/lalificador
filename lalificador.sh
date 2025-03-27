#!/bin/bash

DRY_RUN=false # Modo simulación (no aplica cambios reales)
SCRIPT_PATH="$(readlink -f "$0")"
# ----------------------------------------
# Config
# ----------------------------------------
SIGLAS_DEFAULT="XXX"
CURRENT_DIR_DATE=""
FILES_TO_RENAME=() # arreglo global
# ----------------------------------------
# Funciones
# ----------------------------------------

get_directory_date_from_file() {
   local file="$1"
   local parent_dir=$(basename "$(dirname "$file")")

   # Buscar patrón YYYY.MM.
   if [[ "$parent_dir" =~ ([0-9]{4})\.([0-9]{2}) ]]; then
      echo "${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
   else
      date "+%Y-%m" # fallback
   fi
}

# Extrae sugerencia de nombre válido
suggest_name() {
   local file="$1"
   local base=$(basename "$file")
   local name="${base%.*}"
   local extension="${base##*.}"
   extension=".${extension,,}" # siempre en minúsculas

   local fecha="$CURRENT_DIR_DATE"
   local prefijo="${SIGLAS_OVERRIDE:-$SIGLAS_DEFAULT}"

   # Detectar si empieza por número. (1 a 3 dígitos)
   if [[ "$name" =~ ^([0-9]{1,3})\.(.*)$ ]]; then
      local raw_num="${BASH_REMATCH[1]}"
      local rest="${BASH_REMATCH[2]}"
      local num=$(printf "%03d" $((10#$raw_num)))

      # Extraer parte entre paréntesis (solo uno, completo) (opcional)
      local parentesis=""
      if [[ "$rest" =~ \(.*\) ]]; then
         parentesis=$(echo "$rest" | grep -oE '\([^)]*\)' | head -n1)
         # Eliminar solo espacios tras ( y antes )
         parentesis=$(echo "$parentesis" | sed -E 's/\( */(/; s/ *\)/)/')
      fi

      # Extraer código F.XXXXX (opcional)
      local fcode_raw=$(echo "$rest" | grep -oE 'F\.[A-Za-z0-9]{1,5}' | head -n1)
      local fcode=""
      if [[ -n "$fcode_raw" ]]; then
         local cod=$(echo "$fcode_raw" | cut -d'.' -f2)
         if [[ "$cod" =~ ^[0-9]+$ ]]; then
            # Forzar a decimal evitando octal
            cod=$((10#$cod))
            fcode="F.$(printf "%05d" "$cod")"
         else
            # Alfanumérico: rellenar con ceros por la izquierda si necesario
            while [[ ${#cod} -lt 5 ]]; do cod="0$cod"; done
            fcode="F.$cod"
         fi
      fi

      # Eliminar paréntesis y F. del texto libre
      local libre="$rest"
      libre=$(echo "$libre" | sed -E 's/\(.*?\)//g' | sed -E 's/F\.[A-Za-z0-9]{1,5}//g')

      # Quitar posibles duplicados de fecha y prefijo dentro del texto libre
      libre=$(echo "$libre" | sed -E "s/[0-9]{4}-[0-9]{2}//g" | sed -E "s/${prefijo}//Ig")

      # Limpiar y convertir a snake_case
      libre=$(echo "$libre" | sed -E 's/[^[:alnum:]]+/ /g' | sed -E 's/^ *| *$//g')
      libre=$(echo "$libre" | sed -E 's/ +/_/g' | tr '[:lower:]' '[:upper:]')

      # Componer el nombre final
      local final_name="${num}.${libre}"
      [[ -n "$parentesis" ]] && final_name+=" $parentesis"
      [[ -n "$fcode" ]] && final_name+=" $fcode"
      final_name+=" ${fecha} ${prefijo}${extension}"
      echo "$final_name"
   else
      # Si no empieza por número., usar nombre original sin extensión
      local raw="${name}"

      # Limpiar posibles duplicados
      raw=$(echo "$raw" | sed -E 's/[0-9]{4}[-_][0-9]{2}//g')
      raw=$(echo "$raw" | sed -E "s/${prefijo}//Ig")
      raw=$(echo "$raw" | sed -E 's/ +$//; s/^ +//; s/  +/ /g')

      echo "${raw} ${fecha} ${prefijo}${extension}"
   fi
}

check_filename() {
   local file="$1"
   local filename=$(basename "$file")
   local suggestion=$(suggest_name "$file")

   # Evitar sugerencia vacía (significa que no aplica)
   if [[ -z "$suggestion" ]]; then
      return
   fi

   # Si el nombre actual ya coincide con la sugerencia, está correcto → no mostrar
   if [[ "$filename" == "$suggestion" ]]; then
      return
   fi

   # Solo mostrar si es inválido
   echo "❌ Inválido: $filename -> ✅ $suggestion"
   FILES_TO_RENAME+=("$file|$suggestion")
}

scan_directory() {
   local dir="$1"
   echo "📁 Escaneando: $dir"

   while IFS= read -r -d '' file; do
      # Excluir el propio script
      resolved_file="$(readlink -f "$file")"
      [[ "$resolved_file" == "$SCRIPT_PATH" ]] && continue

      CURRENT_DIR_DATE=$(get_directory_date_from_file "$file")
      check_filename "$file"
   done < <(find "$dir" -type f -print0)
}

wizard_mode() {
   echo "📘 Modo asistente:"
   read -e -p "Introduce el directorio a escanear: " input_dir
   read -p "Introduce las siglas a usar (ej: HOL): " siglas
   SIGLAS_OVERRIDE="$siglas"

   scan_directory "$input_dir"

   echo ""
   if [[ ${#FILES_TO_RENAME[@]} -eq 0 ]]; then
      echo "✅ No hay archivos que necesiten renombrarse."
      return
   fi

   echo "⚠️ Archivos con nombre inválido detectados: ${#FILES_TO_RENAME[@]}"
   read -p "¿Deseas aplicar los cambios sugeridos? [s/N]: " confirm
   if [[ "$confirm" =~ ^[sS]$ ]]; then
      echo "🔄 Renombrando archivos..."
      for entry in "${FILES_TO_RENAME[@]}"; do
         IFS="|" read -r old_path new_name <<<"$entry"
         new_path="$(dirname "$old_path")/$new_name"
         echo "→ $old_path"
         echo "   Renombrado a: $new_path"
         if [[ "$DRY_RUN" == true ]]; then
            echo "   (Simulado) No se renombró por --dry-run"
         else
            mv -i "$old_path" "$new_path"
         fi
      done
      echo "✅ Todos los cambios aplicados."
   else
      echo "❎ No se aplicaron cambios."
   fi
}

show_help() {
   echo ""
   echo "🔧 Uso del script:"
   echo ""
   echo "▶ Modo asistente (por defecto):"
   echo "   ./lalificador.sh"
   echo ""
   echo "▶ Modo directo con flags:"
   echo "   ./lalificador.sh -d <directorio> --siglas <XXX> [--dry-run]"
   echo ""
   echo "   -d, --dir <directorio>  Directorio a escanear"
   echo "   -s, --siglas <XXX>      Siglas a usar (ej: HOL)"
   echo "   --dry-run               Simula la aplicación de cambios"
   echo ""
   echo "▶ Ayuda:"
   echo "   -h, --help              Muestra este mensaje"
   echo ""
}

# ----------------------------------------
# Ejecución principal
# ----------------------------------------

if [[ $# -eq 0 ]]; then
   # Sin argumentos → ejecutar modo asistente
   wizard_mode
   exit 0
fi

# Parseo de flags
dir=""
siglas=""

while [[ $# -gt 0 ]]; do
   case "$1" in
   -d | --dir)
      dir="$2"
      shift 2
      ;;
   -s | --siglas)
      SIGLAS_OVERRIDE="$2"
      shift 2
      ;;
   --dry-run)
      DRY_RUN=true
      shift
      ;;
   -h | --help)
      show_help
      exit 0
      ;;
   *)
      echo "❗ Opción desconocida o incompleta: $1"
      show_help
      exit 1
      ;;
   esac
done

# Si se pasó -d pero no hay ruta válida o faltan siglas, mostrar ayuda
if [[ -n "$dir" && -n "$SIGLAS_OVERRIDE" ]]; then
   scan_directory "$dir"
else
   echo "⚠️  Faltan parámetros obligatorios para ejecución por flags."
   show_help
   exit 1
fi
