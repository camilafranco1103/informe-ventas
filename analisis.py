# analisis.py — versión limpia y robusta

# --- Modo no interactivo para evitar errores de backend en Linux/WSL/servers ---
import matplotlib
matplotlib.use("Agg")  # Comentá esta línea si querés mostrar ventanas gráficas
# -------------------------------------------------------------------------------

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

CSV_PATH = Path("ventas.csv")  # Asegurate que exista en la misma carpeta


def cargar_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        print(f"❌ No encuentro el archivo: {csv_path.resolve()}")
        print("Asegurate de llamarlo ventas.csv o cambia CSV_PATH.")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path, parse_dates=["fecha"])
    except Exception as e:
        print("❌ Error leyendo el CSV:", e)
        print("Verificá encabezados y formato. Encabezados esperados: fecha, producto, cantidad, precio")
        sys.exit(1)

    # Normalizar nombres de columnas
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(" ", "_")
                  .str.replace(r"[^\w_]", "", regex=True)
    )

    # Validar columnas requeridas
    requeridas = {"fecha", "producto", "cantidad", "precio"}
    faltantes = requeridas - set(df.columns)
    if faltantes:
        print(f"❌ Faltan columnas requeridas: {faltantes}")
        print("Encabezados esperados: fecha, producto, cantidad, precio")
        sys.exit(1)

    # Tipos numéricos seguros
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0).astype(int)
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")

    return df


def calcular_metricas(df: pd.DataFrame):
    # Ingreso = cantidad * precio
    df = df.copy()
    df["ingreso"] = df["cantidad"] * df["precio"]

    # Ventas por mes (usar 'ME' para MonthEnd y evitar FutureWarning)
    ventas_mensuales = (
        df.set_index("fecha")
          .resample("ME")["ingreso"]
          .sum()
    )

    # Producto más vendido y por mayores ingresos
    cant_por_producto = (
        df.groupby("producto")["cantidad"]
          .sum()
          .sort_values(ascending=False)
    )
    ingresos_por_producto = (
        df.groupby("producto")["ingreso"]
          .sum()
          .sort_values(ascending=False)
    )

    producto_mas_vendido = cant_por_producto.idxmax()
    cantidad_max = int(cant_por_producto.max())

    producto_top_ingresos = ingresos_por_producto.idxmax()
    ingresos_max = float(ingresos_por_producto.max())

    return {
        "df": df,
        "ventas_mensuales": ventas_mensuales,
        "cant_por_producto": cant_por_producto,
        "ingresos_por_producto": ingresos_por_producto,
        "producto_mas_vendido": producto_mas_vendido,
        "cantidad_max": cantidad_max,
        "producto_top_ingresos": producto_top_ingresos,
        "ingresos_max": ingresos_max,
    }


def graficar_ventas_por_mes(ventas_mensuales: pd.Series, outfile: str = "ventas_por_mes.png"):
    # Etiquetas de mes más legibles
    vm = ventas_mensuales.copy()
    if hasattr(vm.index, "strftime"):
        vm.index = vm.index.strftime("%Y-%m")

    plt.figure()
    vm.plot(kind="bar")
    plt.title("Ventas totales por mes")
    plt.xlabel("Mes")
    plt.ylabel("Ingresos")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(outfile, dpi=120)
    # plt.show()  # habilitá si NO usás backend Agg
    print(f"💾 Gráfico guardado: {outfile}")


def graficar_top5_productos(ingresos_por_producto: pd.Series, outfile: str = "ventas_top5_productos.png"):
    top5 = ingresos_por_producto.head(5)

    plt.figure()
    top5.plot(kind="bar")
    plt.title("Ventas por producto (Top 5 por ingresos)")
    plt.xlabel("Producto")
    plt.ylabel("Ingresos")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outfile, dpi=120)
    # plt.show()  # habilitá si NO usás backend Agg
    print(f"💾 Gráfico guardado: {outfile}")


def exportar_informe(ventas_mensuales, cant_por_producto, ingresos_por_producto,
                     producto_mas_vendido, cantidad_max, producto_top_ingresos, ingresos_max,
                     outfile: str = "informe.txt"):
    with open(outfile, "w", encoding="utf-8") as f:
        f.write("=== Informe de Ventas ===\n\n")

        f.write("Ventas totales por mes (ARS):\n")
        f.write(ventas_mensuales.to_string())
        f.write("\n\n")

        f.write("Producto más vendido (por cantidad):\n")
        f.write(cant_por_producto.to_string())
        f.write(f"\nTOP: {producto_mas_vendido} con {cantidad_max} unidades\n\n")

        f.write("Producto con mayores ingresos:\n")
        f.write(ingresos_por_producto.to_string())
        f.write(f"\nTOP: {producto_top_ingresos} con ingresos = {ingresos_max:.2f}\n\n")

        f.write("Gráficos generados:\n")
        f.write("- ventas_por_mes.png\n")
        f.write("- ventas_top5_productos.png\n")

    print(f"📝 Informe guardado: {outfile}")


def main():
    # 1) Cargar
    df = cargar_csv(CSV_PATH)

    # 2) Calcular métricas
    m = calcular_metricas(df)

    # 3) Mostrar resultados en consola
    print("\n=== Ventas totales por mes ===")
    print(m["ventas_mensuales"])

    print("\n=== Producto más vendido (por cantidad) ===")
    print(m["cant_por_producto"])
    print(f">>> TOP: {m['producto_mas_vendido']} con {m['cantidad_max']} unidades")

    print("\n=== Producto con mayores ingresos ===")
    print(m["ingresos_por_producto"])
    print(f">>> TOP: {m['producto_top_ingresos']} con ingresos = {m['ingresos_max']:.2f}")

    # 4) Gráficos (se guardan como PNG en la carpeta actual)
    graficar_ventas_por_mes(m["ventas_mensuales"], "ventas_por_mes.png")
    graficar_top5_productos(m["ingresos_por_producto"], "ventas_top5_productos.png")

    # 5) Informe de texto (opcional pero útil)
    exportar_informe(
        m["ventas_mensuales"],
        m["cant_por_producto"],
        m["ingresos_por_producto"],
        m["producto_mas_vendido"],
        m["cantidad_max"],
        m["producto_top_ingresos"],
        m["ingresos_max"],
        "informe.txt"
    )


if __name__ == "__main__":
    main()
