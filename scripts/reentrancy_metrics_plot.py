#!/usr/bin/env python3
#
# Script per l'analisi delle metriche di performance (gas e fee) raccolte dal monitoraggio della protezione contro la reentrancy
# 2025
import os                          # Operazioni su filesystem e variabili d'ambiente
import sys                         # Exit in caso di errore
import json                        # Lettura file JSON
import pandas as pd                # Analisi dati con DataFrame
import matplotlib.pyplot as plt    # Creazione grafici
import textwrap                    # Per il wrapping dei testi nelle tabelle

# Configurazione input/output
METRICS_JSON = os.environ.get(
    "METRICS_JSON",
    os.path.join(os.getcwd(), "metrics_output.json")
)
# Directory di output
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
        df_wrapped[col] = df_wrapped[col].astype(str).apply(
            lambda x: '\n'.join(textwrap.wrap(x, col_wrap))
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
        
    # Crea la directory di output se non esiste già
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # --- Controllo: esistenza file di input ---
    if not os.path.isfile(METRICS_JSON):
        print(f"Errore: file di input non trovato: {METRICS_JSON}")
        sys.exit(1)

    PRICE_USD = float(os.environ.get('PRICE_USD', '2000.0'))
    MAX_CALLS = int(os.environ.get('MAX_CALLS', '1000000'))

    # --- Caricamento del JSON di metriche ---
    with open(METRICS_JSON, 'r') as f:
        metrics_data = json.load(f)
    df = pd.DataFrame(metrics_data)

    # --- Analisi del gas ---
    gas_df = df[['contract', 'action', 'gasUsed']].copy()
    if 'iteration' in df.columns:
        gas_df['iteration'] = df['iteration']

    gas_summary = (
        gas_df
        .groupby(['contract', 'action'])['gasUsed']
        .agg(['mean', 'std', 'min', 'max'])
        .reset_index()
    )

    # --- Grafici a barre: gas medio per azione ---
    for action in gas_summary['action'].unique():
        subset = gas_summary[gas_summary['action'] == action]
        plt.figure()
        plt.bar(subset['contract'], subset['mean'])
        plt.xticks(rotation=0)
        plt.title(f"Gas medio per azione {action}")
        plt.ylabel("Gas utilizzato")
        plt.tight_layout()
        out_gas = os.path.join(OUTPUT_DIR, f"gas_medio_{action}.png")
        plt.savefig(out_gas)
        plt.close()
        print(f"Grafico gas medio salvato: {out_gas}")

    # --- Grafico combinato: deploy + 1 chiamata ---
    deploy_mean = gas_summary[gas_summary['action'] == 'deploy'] \
                  .set_index('contract')['mean']
    call_mean = gas_summary[gas_summary['action'] == 'claimReward'] \
                .set_index('contract')['mean']
    
    contracts = sorted(deploy_mean.index)
    if len(contracts) == 2:
        plt.figure()
        plt.bar(contracts, [deploy_mean[c] for c in contracts], color='C0', label='deploy')
        plt.bar(contracts, [call_mean[c] for c in contracts], bottom=[deploy_mean[c] for c in contracts], color='C1', label='claimReward')
        plt.title('Gas deploy + 1 call')
        plt.ylabel('Gas utilizzato')
        plt.legend()
        plt.tight_layout()
        out_dp = os.path.join(OUTPUT_DIR, 'gas_deploy_plus_call.png')
        plt.savefig(out_dp)
        plt.close()
        print(f"Grafico gas_deploy_plus_call salvato: {out_dp}")

    # --- Calcolo percentuale risparmio gas ---
    savings_df = None
    if len(contracts) == 2:
        c1, c2 = contracts
        perc_deploy = (deploy_mean[c1] - deploy_mean[c2]) / deploy_mean[c1] * 100
        perc_claim = (call_mean[c1] - call_mean[c2]) / call_mean[c1] * 100
        savings_df = pd.DataFrame({
            'action': ['deploy', 'claimReward'],
            c1: [deploy_mean[c1], call_mean[c1]],
            c2: [deploy_mean[c2], call_mean[c2]],
            'risparmio %': [perc_deploy, perc_claim]
        })
        print('### PERCENTUALE RISPARMIO GAS ###')
        print(savings_df.to_string(index=False, float_format=lambda x: f"{x:.2f}%"))

    # --- Grafico cumulativo costo gas vs numero di chiamate ---
    if savings_df is not None:
        n_calls = list(range(0, MAX_CALLS))
        cum_c1 = [deploy_mean[c1] + n * call_mean[c1] for n in n_calls]
        cum_c2 = [deploy_mean[c2] + n * call_mean[c2] for n in n_calls]
        plt.figure()
        plt.plot(n_calls, cum_c1, label=c1)
        plt.plot(n_calls, cum_c2, label=c2)
        plt.xlabel("Numero di chiamate claimReward")
        plt.ylabel("Costo totale del gas")
        plt.title("Costo gas cumulativo vs numero di chiamate")
        plt.legend()
        plt.tight_layout()
        cum_out = os.path.join(OUTPUT_DIR, "costo_gas_cumulativo.png")
        plt.savefig(cum_out)
        plt.close()
        print(f"Grafico costo gas cumulativo salvato: {cum_out}")

    # --- Analisi fee e definizione di fee_summary ---
    fee_df = df.copy()
    fee_df['gasUsed'] = fee_df['gasUsed'].astype(int)
    fee_df['feeWei'] = fee_df['feeWei'].astype(int)
    fee_df['feeETH'] = fee_df['feeWei'] / 1e18
    fee_df['feeUSD'] = fee_df['feeETH'] * PRICE_USD

    fee_summary = (
        fee_df
        .groupby(['contract', 'action'])
        .agg(
            avgGas=('gasUsed', 'mean'),
            avgFeeETH=('feeETH', 'mean'),
            avgFeeUSD=('feeUSD', 'mean')
        )
        .reset_index()
    )
    print('### RIEPILOGO FEE ###')
    print(fee_summary.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

    # --- Grafici fee medie ---
    for metric, label in [("avgFeeETH", "ETH"), ("avgFeeUSD", "USD")]:
        pivot = fee_summary.pivot(index='contract', columns='action', values=metric)
        plt.figure()
        pivot.plot(kind='bar', rot=0)
        plt.legend(framealpha=0.75) 
        plt.title(f"Fee media per azione ({label})")
        plt.ylabel(f"Fee in {label}")
        plt.tight_layout()
        out_fee = os.path.join(OUTPUT_DIR, f"fee_media_{label.lower()}.png")
        plt.savefig(out_fee)
        plt.close()
        print(f"Grafico fee salvato: {out_fee}")

    # --- Analisi dimensioni bytecode e payload ---
    size_df = fee_df[['contract', 'action', 'txSizeBytes']].copy()
    bytecode_df = fee_df[fee_df['action'] == 'deploy'][['contract', 'bytecodeSizeBytes']].drop_duplicates()

    plt.figure()
    plt.bar(bytecode_df['contract'], bytecode_df['bytecodeSizeBytes'])
    plt.xticks(rotation=0)
    plt.title("Dimensione del bytecode (Byte)")
    plt.ylabel("Byte")
    plt.tight_layout()
    out_bytecode = os.path.join(OUTPUT_DIR, "dimensione_bytecode.png")
    plt.savefig(out_bytecode)
    plt.close()
    print(f"Grafico dimensione bytecode salvato: {out_bytecode}")

    gas_tab = gas_summary.copy()
    fee_tab = fee_summary.copy()

    create_table_metrics(
        gas_tab[['contract', 'action', 'mean', 'std', 'min', 'max']],
        os.path.join(OUTPUT_DIR, 'tabella_riepilogo_utilizzo_gas.png')
    )
 
    if savings_df is not None:
        create_table_metrics(
            savings_df,
            os.path.join(OUTPUT_DIR, 'tabella_percentuale_risparmio_gas.png')
        )
        
    create_table_metrics(
        fee_tab[['contract', 'action', 'avgGas', 'avgFeeETH', 'avgFeeUSD']],
        os.path.join(OUTPUT_DIR, 'tabella_riepilogo_fee.png')
    )

if __name__ == '__main__':
    main()
