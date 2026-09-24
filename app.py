import base64
import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
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
    map_html = ''
    plot_chronic = ''
    plot_quality = ''
    chronic_top = []
    prevention_points = []
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

        # Target 1: Titik rawan (sebaran) - choropleth peta dunia
        if 'new_cases_per_million' in df_countries.columns:
            map_df = (
                df_countries.groupby('location')
                .agg(
                    iso_code=('iso_code', 'first'),
                    continent=('continent', 'first'),
                    total_cases=('total_cases', 'max'),
                    new_cases_per_million=('new_cases_per_million', 'max'),
                    total_deaths=('total_deaths', 'max'),
                )
                .reset_index()
            )
            fig_map = px.choropleth(
                map_df,
                locations='iso_code',
                color='total_cases',
                hover_name='location',
                hover_data={
                    'iso_code': False,
                    'continent': True,
                    'total_cases': ':,.0f',
                    'new_cases_per_million': ':,.0f',
                    'total_deaths': ':,.0f',
                },
                color_continuous_scale='Reds',
                projection='natural earth',
                title='Sebaran Total Kasus COVID-19 per Negara (Titik Rawan)',
            )
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                coloraxis_colorbar=dict(title='Total Kasus'),
            )
            map_html = fig_map.to_html(
                full_html=False, include_plotlyjs='cdn'
            )

        # Target 2: Beban penyakit kronis (chronic disease burden)
        if 'diabetes_prevalence' in df_countries.columns and 'cardiovasc_death_rate' in df_countries.columns:
            chronic = (
                df_countries.groupby('location')
                .agg(
                    diabetes=('diabetes_prevalence', 'max'),
                    cardio=('cardiovasc_death_rate', 'max'),
                )
                .dropna()
                .reset_index()
            )
            chronic = chronic[chronic['diabetes'] > 0]
            chronic['skor_kronis'] = chronic['diabetes'] + chronic['cardio'] / 100
            chronic_top = (
                chronic.sort_values('skor_kronis', ascending=False)
                .head(15)[['location', 'diabetes', 'cardio']]
                .values.tolist()
            )

            fig, ax = plt.subplots(figsize=(10, 6))
            top15 = chronic.sort_values('skor_kronis', ascending=False).head(15)
            ax.barh(
                top15['location'][::-1],
                top15['diabetes'][::-1],
                color='#fd7e14',
                label='Prevalensi Diabetes (%)',
            )
            ax.barh(
                top15['location'][::-1],
                (top15['cardio'] / 100)[::-1],
                color='#dc3545',
                alpha=0.7,
                label='Rate Kematian Kardiovaskuler (dibagi 100)',
            )
            ax.set_title('Beban Penyakit Kronis Tertinggi (Diabetes & Kardiovaskuler)')
            ax.set_xlabel('Nilai (baca legenda)')
            ax.legend(fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            img_chronic = io.BytesIO()
            fig.savefig(img_chronic, format='png')
            img_chronic.seek(0)
            plot_chronic = base64.b64encode(img_chronic.getvalue()).decode('utf-8')
            plt.close(fig)

            # Komorbiditas vs keparahan COVID (CFR)
            chronic_cfr = chronic.merge(
                cfr_data[['location', 'cfr']], on='location', how='inner'
            )
            if len(chronic_cfr) > 10:
                r_comorbid = chronic_cfr['skor_kronis'].corr(chronic_cfr['cfr'])
                prevention_points.append(
                    f'Korelasi beban penyakit kronis dengan CFR COVID (r = {r_comorbid:.2f}): '
                    'negara/kota dengan tingkat penyakit kronis tinggi perlu prioritas '
                    'pencegahan & kapasitas RS lebih besar.'
                )

        # Target 4: Insight untuk strategi kesehatan preventif
        if vaccine_r:
            r_val = float(vaccine_r)
            if r_val < 0:
                prevention_points.append(
                    'Cakupan vaksinasi tinggi berkorelasi negatif dengan kematian '
                    '(r = {:.2f}) -> perkuat program imunisasi & booster sebagai pencegahan.'.format(r_val)
                )
            else:
                prevention_points.append(
                    'Korelasi vaksinasi vs kematian positif (r = {:.2f}) -> indikasi '
                    'pengaruh faktor usia/pendapatan; tetap dorong vaksin + skrining komorbid.'.format(r_val)
                )
        if chronic_top:
            d_top = chronic_top[0]
            prevention_points.append(
                f'Prioritas skrining penyakit kronis per negara, mulai dari {d_top[0]} '
                f'(diabetes {d_top[1]:.1f}%). Deteksi dini = pencegahan komplikasi.'
            )

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

    # Target 3: Kesenjangan kualitas data (% data kosong pada kolom klinis utama)
    quality_cols = [
        'new_cases', 'total_deaths', 'reproduction_rate',
        'icu_patients', 'hosp_patients', 'total_tests', 'total_vaccinations',
        'diabetes_prevalence', 'cardiovasc_death_rate', 'life_expectancy',
    ]
    quality_cols = [c for c in quality_cols if c in df.columns]
    pct_missing = (df[quality_cols].isnull().mean() * 100).sort_values().round(1)
    if len(pct_missing) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(
            pct_missing.index,
            pct_missing.values,
            color=pct_missing.apply(
                lambda x: '#dc3545' if x >= 50 else ('#fd7e14' if x >= 20 else '#198754')
            ),
        )
        ax.set_title('Kesenjangan Kualitas Data: % Data Kosong per Kolom Klinis')
        ax.set_xlabel('% Data Kosong (Missing)')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        img_quality = io.BytesIO()
        fig.savefig(img_quality, format='png')
        img_quality.seek(0)
        plot_quality = base64.b64encode(img_quality.getvalue()).decode('utf-8')
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
        map_html=map_html,
        plot_chronic=plot_chronic,
        chronic_top=chronic_top,
        plot_quality=plot_quality,
        prevention_points=prevention_points,
    )


if __name__ == '__main__':
    # use_reloader=False dimatikan agar tidak melakukan restart otomatis
    app.run(debug=True, use_reloader=False)
    