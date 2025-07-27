#!/usr/bin/env python3
#
# Script per l'analisi delle metriche di performance raccolte dal monitoraggio dell'oracle aggregatore.
# 2025
import os                          # Operazioni su filesystem e variabili d'ambiente
import sys                         # Exit in caso di errore
import json                        # Lettura e parsing file JSON
import pandas as pd                # Analisi dati tabulari con DataFrame
import matplotlib.pyplot as plt    # Creazione di grafici
import textwrap                    # Wrapping di testi nelle celle delle tabelle

# Configurazione input/output
METRICS_JSON = os.environ.get(
    "METRICS_JSON",
    os.path.join(os.getcwd(), "metrics_output.json")
)
OUTPUT_DIR = os.environ.get(
    "OUTPUT_DIR",
    os.path.dirname(METRICS_JSON) or os.getcwd()
)

# ----------------------------------------------------------------------------
# Funzione di utilità: salva DataFrame come PNG
# ----------------------------------------------------------------------------
def create_table_metrics(df, filename, col_wrap=30, fontsize=8):
        
    base = os.path.basename(filename)
    if 'riepilogo_utilizzo_gas' in base:
        title = "Riepilogo Utilizzo Gas"
    elif 'percentuale_risparmio_gas' in base:
        title = "Percentuale Risparmio Gas"
    elif 'riepilogo_fee' in base:
        title = "Riepilogo Fee"
    else:
        title = None

    df_wrapped = df.copy()
    for col in df_wrapped.select_dtypes(include='object').columns:
        df_wrapped[col] = (
            df_wrapped[col]
            .astype(str)
            .apply(lambda x: '\n'.join(textwrap.wrap(x, col_wrap)))
        )

    ncols = len(df_wrapped.columns)
    nrows = len(df_wrapped)
    fig_width = max(6, ncols * 1.5)
    fig_height = max(1 + nrows * 0.5 + (0.3 if title else 0), 2)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')

    if title:
        fig.suptitle(title, fontsize=fontsize+2, y=0.63)

    tbl = ax.table(
        cellText=df_wrapped.values,
        colLabels=df_wrapped.columns,
        cellLoc='center',
        loc='center'
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(fontsize)
    tbl.auto_set_column_width(col=list(range(len(df_wrapped.columns))))
    tbl.scale(1, 1.2)

    plt.tight_layout(rect=[0, 0, 1, 0.90] if title else None)
    fig.savefig(filename, dpi=200)
    plt.close(fig)
    print(f"Tabella salvata: {filename}")


# ----------------------------------------------------------------------------
# Funzione principale
# ----------------------------------------------------------------------------
def main():
    # Crea OUTPUT_DIR (directory di output) se non esiste
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    PRICE_USD = float(os.environ.get("PRICE_USD", "2000.0"))
    MAX_CALLS = int(os.environ.get("MAX_CALLS", "100"))

    # Verifica che METRICS_JSON (default 'metrics_output.json') esista
    if not os.path.isfile(METRICS_JSON):
        print(f"Errore: file di input non trovato: {METRICS_JSON}")
        sys.exit(1)
        
    # Carica i dati in DataFrame
    with open(METRICS_JSON, "r") as f:
        data = json.load(f)
    full_df = pd.DataFrame(data)

    # Analisi Gas: estrazione colonne rilevanti e calcolo statistiche di base
    gas_df = full_df[["contract", "action", "iteration", "gasUsed"]].copy()
    fee_df = full_df.copy()
    
    # Conversione fee da Wei a ETH e in USD
    fee_df["feeETH"] = pd.to_numeric(fee_df["feeWei"]) / 1e18
    fee_df["feeUSD"] = fee_df["feeETH"] * PRICE_USD

    # Statistiche gas per contract/action
    gas_summary = (
        gas_df
        .groupby(["contract", "action"])["gasUsed"]
        .agg(['mean', 'std', 'min', 'max'])
        .reset_index()
    )

    # Grafico del gas medio per ogni azione
    for action in gas_summary["action"].unique():
        subset = gas_summary[gas_summary["action"] == action]
        plt.figure()
        plt.bar(subset["contract"], subset["mean"])
        plt.title(f"Gas medio per azione {action}")
        plt.ylabel("Gas utilizzato")
        plt.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"gas_medio_{action}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Grafico gas medio salvato: {out_path}")

    # Calcolo e tabella della percentuale di risparmio gas 
    deploy_mean = gas_summary[gas_summary["action"] == "deploy"].set_index("contract")["mean"]
    call_mean = gas_summary[gas_summary["action"] == "aggregateQuotes"].set_index("contract")["mean"]
    contracts = sorted(deploy_mean.index)
    savings_df = None
    if len(contracts) == 2:
        c1, c2 = contracts
        perc_deploy = (deploy_mean[c1] - deploy_mean[c2]) / deploy_mean[c1] * 100
        perc_call = (call_mean[c1] - call_mean[c2]) / call_mean[c1] * 100
        savings_df = pd.DataFrame({
            "action": ["deploy", "aggregateQuotes"],
            c1: [deploy_mean[c1], call_mean[c1]],
            c2: [deploy_mean[c2], call_mean[c2]],
            "risparmio %": [perc_deploy, perc_call]
        })
        print("\n### PERCENTUALE RISPARMIO GAS ###")
        print(savings_df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        # Salvataggio tabella risparmio gas
        create_table_metrics(
            savings_df,
            os.path.join(OUTPUT_DIR, 'tabella_percentuale_risparmio_gas.png')
        )

    # Grafico combinato: gas di deploy + una chiamata aggregateQuotes
    plt.figure()
    for i, contract in enumerate(deploy_mean.index):
        plt.bar(
            contract,
            deploy_mean[contract],
            color='C0', label='deploy' if i == 0 else ""
        )
        plt.bar(
            contract,
            call_mean[contract],
            bottom=deploy_mean[contract],
            color='C1', label='call' if i == 0 else ""
        )
    plt.title("Gas deploy + una chiamata aggregateQuotes")
    plt.ylabel("Gas utilizzato")
    plt.legend()
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "gas_deploy_plus_call.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Grafico gas deploy+call salvato: {out_path}")

    # Grafico del costo cumulativo (0…MAX_CALLS chiamate aggregateQuotes)
    if savings_df is not None:
        n_calls = list(range(0, MAX_CALLS + 1))
        cum1 = [deploy_mean[c1] + n * call_mean[c1] for n in n_calls]
        cum2 = [deploy_mean[c2] + n * call_mean[c2] for n in n_calls]
        plt.figure()
        plt.plot(n_calls, cum1, label=c1)
        plt.plot(n_calls, cum2, label=c2)
        plt.xlabel("Numero di chiamate aggregateQuotes")
        plt.ylabel("Costo totale del gas")
        plt.title("Costo cumulativo vs numero di chiamate")
        plt.legend()
        plt.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, "costo_gas_cumulativo.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Grafico costo gas cumulativo salvato: {out_path}")

    # Analisi delle fee: conversione da Wei a ETH e USD
    fee_summary = (
        fee_df
        .groupby(["contract", "action"])
        .agg(
            avgGas=("gasUsed", 'mean'),
            avgFeeETH=("feeETH", 'mean'),
            avgFeeUSD=("feeUSD", 'mean')
        )
        .reset_index()
    )

    # Grafici delle fee medie per azione (ETH vs USD)
    for metric, label in [("avgFeeETH", "ETH"), ("avgFeeUSD", "USD")]:
        pivot = fee_summary.pivot(index='contract', columns='action', values=metric)
        plt.figure()
        pivot.plot(kind='bar', rot=0)
        plt.legend(framealpha=0.25)
        plt.title(f"Fee media per azione ({label})")
        plt.ylabel(f"Fee in {label}")
        plt.tight_layout()
        out_fee = os.path.join(OUTPUT_DIR, f"fee_media_{label.lower()}.png")
        plt.savefig(out_fee)
        plt.close()
        print(f"Grafico fee media salvato: {out_fee}")

    # Grafico della dimensione del bytecode (azione 'deploy')
    bytecode_df = (
        fee_df[fee_df["action"] == "deploy"]
        [["contract", "bytecodeSizeBytes"]]
        .drop_duplicates()
    )
    plt.figure()
    plt.bar(bytecode_df["contract"], bytecode_df["bytecodeSizeBytes"])
    plt.title("Dimensione del bytecode (Byte)")
    plt.ylabel("Byte")
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "dimensione_bytecode.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Grafico bytecode salvato: {out_path}")

    print("\n### RIEPILOGO UTILIZZO GAS ###")
    print(gas_summary.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
   
    # Salvataggio tabella riepilogo in PNG
    create_table_metrics(
        gas_summary,
        os.path.join(OUTPUT_DIR, 'tabella_riepilogo_utilizzo_gas.png')
    )

    print("\n### RIEPILOGO FEE ###")
    print(fee_summary.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    create_table_metrics(
        fee_summary,
        os.path.join(OUTPUT_DIR, 'tabella_riepilogo_fee.png')
    )

if __name__ == "__main__":
    main()
