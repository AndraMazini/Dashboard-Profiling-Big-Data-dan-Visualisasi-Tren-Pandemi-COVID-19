import base64
import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# Load data dan buat sampel 1x saja saat server pertama kali dinyalakan
print('Sedang memuat data 96 MB, tunggu sebentar...')
df = pd.read_csv('data/WDI.csv')
df.sample(frac=0.01, random_state=42).to_csv(
    'data/WDI_sample.csv', index=False
)
print('Data berhasil dimuat!')


@app.route('/')
def dashboard():
    rows, cols = df.shape
    memory_mb = round(df.memory_usage(deep=True).sum() / (1024**2), 2)

    missing = (
        df.isnull()
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .values.tolist()
    )

    plot_url = ''
    plot_countries = ''
    top_countries = []
    bottom_countries = []
    plot_cfr = ''
    plot_vaccine = ''
    vaccine_r = ''
    plot_continent = ''
    if 'location' in df.columns and 'total_cases' in df.columns and 'total_deaths' in df.columns and 'iso_code' in df.columns:
        df_countries = df[
            df['iso_code'].notna()
            & ~df['iso_code'].str.startswith('OWID_', na=False)
        ]
        country_stats = (
            df_countries.groupby('location')[['total_cases', 'total_deaths']]
            .max()
            .sort_values('total_cases', ascending=False)
            .reset_index()
        )
        top10 = country_stats.head(10)
        bottom10 = country_stats[country_stats['total_cases'] > 0].tail(10)

        top_countries = top10[['location', 'total_cases', 'total_deaths']].values.tolist()
        bottom_countries = bottom10[['location', 'total_cases', 'total_deaths']].values.tolist()

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes[0].barh(
            top10['location'][::-1],
            top10['total_cases'][::-1],
            color='#dc3545',
        )
        axes[0].set_title('10 Negara Terdampak Terbanyak')
        axes[0].set_xlabel('Total Kasus')
        axes[0].grid(True, linestyle='--', alpha=0.5)

        axes[1].barh(
            bottom10['location'][::-1],
            bottom10['total_cases'][::-1],
            color='#198754',
        )
        axes[1].set_title('10 Negara Terdampak Paling Sedikit')
        axes[1].set_xlabel('Total Kasus')
        axes[1].grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        img_countries = io.BytesIO()
        fig.savefig(img_countries, format='png')
        img_countries.seek(0)
        plot_countries = base64.b64encode(img_countries.getvalue()).decode('utf-8')
        plt.close(fig)

        # Analisis 1: Case Fatality Rate (CFR) per negara
        cfr_data = country_stats[country_stats['total_cases'] >= 100000].copy()
        cfr_data['cfr'] = cfr_data['total_deaths'] / cfr_data['total_cases'] * 100
        cfr_top = cfr_data.sort_values('cfr', ascending=False).head(15)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(
            cfr_top['location'][::-1],
            cfr_top['cfr'][::-1],
            color='#6f42c1',
        )
        ax.set_title('15 Negara dengan Case Fatality Rate (CFR) Tertinggi')
        ax.set_xlabel('CFR (%) — Kematian / Kasus')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        img_cfr = io.BytesIO()
        fig.savefig(img_cfr, format='png')
        img_cfr.seek(0)
        plot_cfr = base64.b64encode(img_cfr.getvalue()).decode('utf-8')
        plt.close(fig)

        # Analisis 2: Korelasi vaksinasi vs tingkat kematian per negara
        if 'people_fully_vaccinated_per_hundred' in df_countries.columns and 'total_deaths_per_million' in df_countries.columns:
            vax_df = (
                df_countries.groupby('location')
                .agg(
                    continent=('continent', 'first'),
                    fully_vax=('people_fully_vaccinated_per_hundred', 'max'),
                    deaths_per_million=('total_deaths_per_million', 'max'),
                )
                .dropna()
                .reset_index()
            )
            if len(vax_df) > 10:
                r = vax_df['fully_vax'].corr(vax_df['deaths_per_million'])
                vaccine_r = f'{r:.2f}'

                fig, ax = plt.subplots(figsize=(9, 6))
                for cont, g in vax_df.groupby('continent'):
                    ax.scatter(
                        g['fully_vax'],
                        g['deaths_per_million'],
                        label=cont,
                        s=18,
                        alpha=0.6,
                    )
                ax.set_title(f'Korelasi Vaksinasi vs Kematian per Juta Penduduk (r = {r:.2f})')
                ax.set_xlabel('Orang Divaksin Penuh per 100 Penduduk (%)')
                ax.set_ylabel('Total Kematian per Juta Penduduk')
                ax.legend(fontsize=8)
                ax.grid(True, linestyle='--', alpha=0.5)
                plt.tight_layout()
                img_vaccine = io.BytesIO()
                fig.savefig(img_vaccine, format='png')
                img_vaccine.seek(0)
                plot_vaccine = base64.b64encode(img_vaccine.getvalue()).decode('utf-8')
                plt.close(fig)

    # Analisis 3: Tren kasus baru per kontinen (agregasi bulanan)
    if 'date' in df.columns and 'new_cases_per_million' in df.columns and 'continent' in df.columns:
        cont = df[df['continent'].notna()].copy()
        cont['date'] = pd.to_datetime(cont['date'])
        cont = cont.set_index('date')
        monthly = (
            cont.groupby(['continent', pd.Grouper(freq='ME')])['new_cases_per_million']
            .sum()
            .reset_index()
        )

        fig, ax = plt.subplots(figsize=(10, 5))
        for cname, g in monthly.groupby('continent'):
            ax.plot(g['date'], g['new_cases_per_million'], label=cname, linewidth=1.5)
        ax.set_title('Tren Kasus Baru per Kontinen (Agregasi Bulanan)')
        ax.set_xlabel('Tanggal')
        ax.set_ylabel('Kasus per Juta Penduduk (Total per Bulan)')
        ax.legend(fontsize=8, ncol=2)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        img_continent = io.BytesIO()
        fig.savefig(img_continent, format='png')
        img_continent.seek(0)
        plot_continent = base64.b64encode(img_continent.getvalue()).decode('utf-8')
        plt.close(fig)

    if 'date' in df.columns and 'new_cases' in df.columns:
        df_temp = df.copy()
        df_temp['Year'] = pd.to_datetime(df_temp['date']).dt.year
        yearly = df_temp.groupby('Year')['new_cases'].sum().reset_index()

        plt.figure(figsize=(8, 4))
        plt.plot(
            yearly['Year'],
            yearly['new_cases'],
            marker='o',
            color='#0d6efd',
            linewidth=2,
        )
        plt.title('Total New Cases by Year Globally')
        plt.xlabel('Year')
        plt.ylabel('Total New Cases')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

    return render_template(
        'index.html',
        rows=f'{rows:,}',
        cols=cols,
        memory=memory_mb,
        missing=missing,
        plot_url=plot_url,
        plot_countries=plot_countries,
        top_countries=top_countries,
        bottom_countries=bottom_countries,
        plot_cfr=plot_cfr,
        plot_vaccine=plot_vaccine,
        vaccine_r=vaccine_r,
        plot_continent=plot_continent,
    )


if __name__ == '__main__':
    # use_reloader=False dimatikan agar tidak melakukan restart otomatis
    app.run(debug=True, use_reloader=False)
    