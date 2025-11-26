import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from PIL import Image
import os

# Configuração da Página
st.set_page_config(
    page_title="Dinâmica Veicular - Atividade 02",
    page_icon="🚗",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES E CLASSE VEÍCULO ---
class Vehicle:
    def __init__(self, M, L, b, c, h, Af, Cd, fr, rho, drive_type, tire_radius, gear_ratios, final_drive, eta_d):
        self.M = M
        self.g = 9.81
        self.W = M * self.g
        self.L = L
        self.b = b
        self.c = c
        self.h = h
        self.Af = Af
        self.Cd = Cd
        self.fr = fr
        self.rho = rho
        self.drive_type = drive_type
        self.tire_radius = tire_radius
        self.gear_ratios = gear_ratios
        self.final_drive = final_drive
        self.eta_d = eta_d

    def dynamic_loads(self, ax, theta_rad):
        # ax positivo = aceleração, negativo = frenagem
        W = self.W
        L, c, b, h = self.L, self.c, self.b, self.h
        
        # Cargas Estáticas na rampa (sem inércia)
        Wf_stat = (c / L) * W * np.cos(theta_rad) - (h / L) * W * np.sin(theta_rad)
        Wr_stat = (b / L) * W * np.cos(theta_rad) + (h / L) * W * np.sin(theta_rad)

        # Transferência de Carga Longitudinal devido à aceleração ax
        Delta_W_inertia = (h / L) * (ax * self.M)
        
        Wf = Wf_stat - Delta_W_inertia
        Wr = Wr_stat + Delta_W_inertia
        
        return Wf, Wr

    def max_tractive_force(self, Wf, Wr, mu):
        if self.drive_type == 'FWD (Tração Dianteira)':
            Fmax = mu * Wf
        elif self.drive_type == 'RWD (Tração Traseira)':
            Fmax = mu * Wr
        elif self.drive_type == 'AWD (Tração Integral)':
            Fmax = mu * (Wf + Wr) 
        else:
            Fmax = 0
        return Fmax

# Função auxiliar para carregar imagens com segurança
def show_jazar_image(filename, caption):
    with st.expander(f"📘 Ver Diagrama de Referência (Jazar): {caption}"):
        if os.path.exists(filename):
            st.image(filename, caption=caption, use_container_width=True)
        else:
            st.warning(f"Imagem '{filename}' não encontrada. Adicione o print do livro na pasta.")

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        image = Image.open("chevrolet-onix-plus-lt-turbo-mt-2025-5.jpg")
        st.image(image, caption='Chevrolet Onix Plus', use_container_width=True)
    except:
        st.warning("Imagem do Onix não encontrada.")

    st.markdown("---")
    st.header("⚙️ Parâmetros do Veículo")

    M = st.number_input("Massa Total (kg)", value=1117.0, step=10.0, format="%.1f")
    L = st.number_input("Distância Entre-Eixos (m)", value=2.55, step=0.01, format="%.2f")
    
    col_cg1, col_cg2 = st.columns(2)
    with col_cg1:
        b = st.number_input("Dist. CG ao Eixo Diant. 'b' (m)", value=1.10, step=0.01, format="%.2f")
    with col_cg2:
        c = L - b
        st.metric("Dist. CG ao Eixo Tras. 'c'", f"{c:.2f} m")

    h = st.number_input("Altura do CG 'h' (m)", value=0.55, step=0.01, format="%.2f")
    t = st.number_input("Bitola (Largura) 't' (m)", value=1.50, step=0.01, format="%.2f")
    ty = st.number_input("Desvio Lateral do CG 'ty' (m)", value=0.00, step=0.01, help="Positivo = Esquerda. 0 = Centro.")

    st.markdown("---")
    st.subheader("Aerodinâmica e Pneus")
    Af = st.number_input("Área Frontal (m²)", value=2.1, step=0.1, format="%.1f")
    Cd = st.number_input("Coef. Arrasto (Cd)", value=0.32, step=0.01, format="%.2f")
    fr = st.number_input("Resist. Rolamento (fr)", value=0.015, step=0.001, format="%.3f")

# --- CORPO PRINCIPAL ---
st.title("🚗 Simulador de Dinâmica Veicular")
st.markdown("**Atividade 02 - Modelagem baseada em Jazar**")

st.markdown("### 📌 Selecione o Modelo de Análise:")
analysis_mode = st.selectbox(
    "Modo",
    [
        "🚗 Dinâmica Longitudinal (Aceleração)",
        "🅿️ Veículo Parado (Plano e Inclinado)",
        "🔄 Veículo em Curva (Banked Road)",
        "🛑 Frenagem (Ideal e Eixo Simples)",
        "🚛 Veículo com Trailer (Inclinado)"
    ],
    label_visibility="collapsed"
)
st.markdown("---")

g = 9.81
W = M * g

# ==============================================================================
# MODO 1: ACELERAÇÃO
# ==============================================================================
if analysis_mode == "🚗 Dinâmica Longitudinal (Aceleração)":
    st.header("🚗 Aceleração em Pista Plana e Inclinada")
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔧 Powertrain")
        drive_type = st.selectbox("Tração", ['FWD (Tração Dianteira)', 'RWD (Tração Traseira)', 'AWD (Tração Integral)'])
        mu = st.slider("Coef. Atrito (μ)", 0.1, 1.2, 0.85, 0.05)
        
        with st.expander("Detalhes da Transmissão"):
            tire_radius = st.number_input("Raio Pneu (m)", 0.30)
            final_drive = st.number_input("Diferencial", 4.0)
            eta_d = st.number_input("Eficiência", 0.90)
            num_gears = st.number_input("Qtd Marchas", 5, step=1)
            gear_ratios = []
            default_ratios = [3.5, 2.1, 1.4, 1.0, 0.8]
            for i in range(num_gears):
                 val = default_ratios[i] if i < len(default_ratios) else 0.7
                 gear_ratios.append(st.number_input(f"Marcha {i+1}", val))
            
            torque_max = st.number_input("Torque Máx (Nm)", 160.0)
            rpm_torque_max = st.number_input("RPM Torque", 2000.0)
            power_max_hp = st.number_input("Potência (cv)", 116.0)
            rpm_power_max = st.number_input("RPM Potência", 5500.0)
            rpm_limit = st.number_input("RPM Corte", 6500.0)

    vehicle = Vehicle(M, L, b, c, h, Af, Cd, fr, 1.225, drive_type, tire_radius, gear_ratios, final_drive, eta_d)

    tab1, tab2 = st.tabs(["⛰️ Rampa e Limites", "📈 Gráficos de Desempenho"])

    with tab1:
        st.subheader("Modelo Matemático (Cargas Dinâmicas)")
        show_jazar_image("jazar_accel_grade.png", "Accelerating Car on an Inclined Road")

        st.latex(r"W_f = \frac{W}{L}(c \cos\theta - h \sin\theta) - \frac{h}{L} m a_x")
        st.latex(r"W_r = \frac{W}{L}(b \cos\theta + h \sin\theta) + \frac{h}{L} m a_x")

        c1, c2 = st.columns(2)
        theta_deg = c1.slider("Ângulo da Rampa (°)", 0.0, 30.0, 5.0, 0.5)
        ax_sim = c2.slider("Aceleração Desejada (m/s²)", 0.0, 5.0, 1.5)
        theta_rad = np.radians(theta_deg)

        Wf_dyn, Wr_dyn = vehicle.dynamic_loads(ax_sim, theta_rad)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Carga Dianteira", f"{Wf_dyn:.0f} N")
        k2.metric("Carga Traseira", f"{Wr_dyn:.0f} N")
        k3.metric("Peso Total", f"{W:.0f} N")

        st.subheader("Limite de Tração")
        F_trac_max = vehicle.max_tractive_force(Wf_dyn, Wr_dyn, mu)
        F_resist_start = W * np.sin(theta_rad) + fr * W * np.cos(theta_rad)
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Tração Máxima Disp.", f"{F_trac_max:.0f} N")
        col_res2.metric("Resistência (Grade+Roll)", f"{F_resist_start:.0f} N")

        if F_trac_max > F_resist_start:
            amax_possible = (F_trac_max - F_resist_start) / M
            st.success(f"✅ Arranca com sucesso! Aceleração máx possível: {amax_possible:.2f} m/s²")
        else:
            st.error("❌ Patina na largada.")

        # --- NOVO GRÁFICO: Transferência de Carga vs Aceleração e Inclinação ---
        st.markdown("---")
        st.subheader("📊 Gráfico: Transferência de Carga (Aceleração vs. Inclinação)")
        st.caption(f"Este gráfico mostra como as cargas nos eixos variam conforme a aceleração aumenta, para a inclinação fixa definida acima ({theta_deg}°).")

        # Gerar dados simulados para uma faixa de acelerações
        accel_range = np.linspace(0, 5, 50)  # De 0 a 5 m/s²
        data_transfer = []

        for ax_val in accel_range:
            wf_i, wr_i = vehicle.dynamic_loads(ax_val, theta_rad)
            data_transfer.append({'Aceleração (m/s²)': ax_val, 'Carga (N)': wf_i, 'Eixo': 'Dianteiro (Wf)'})
            data_transfer.append({'Aceleração (m/s²)': ax_val, 'Carga (N)': wr_i, 'Eixo': 'Traseiro (Wr)'})

        df_transfer = pd.DataFrame(data_transfer)

        # Criar gráfico interativo com Altair
        chart_transfer = alt.Chart(df_transfer).mark_line(strokeWidth=3).encode(
            x='Aceleração (m/s²)',
            y=alt.Y('Carga (N)', scale=alt.Scale(zero=False)), # Escala dinâmica para ver melhor a variação
            color='Eixo',
            tooltip=['Aceleração (m/s²)', 'Carga (N)', 'Eixo']
        ).interactive()

        # Adicionar linha vertical na aceleração atual selecionada pelo slider
        rule_ax = alt.Chart(pd.DataFrame({'x': [ax_sim]})).mark_rule(color='red', strokeDash=[5,5]).encode(x='x')
        text_ax = alt.Chart(pd.DataFrame({'x': [ax_sim], 'y': [Wf_dyn], 'text': ['Ponto Atual']})).mark_text(align='left', dx=5, dy=-5, color='red').encode(x='x', y='y', text='text')

        st.altair_chart(chart_transfer + rule_ax + text_ax, use_container_width=True)
        st.info("💡 **Análise:** Note que ao aumentar o slider de *Ângulo da Rampa*, as linhas de carga inicial (Aceleração=0) se deslocam (peso vai para trás), alterando o ponto de partida das curvas.")


    with tab2:
        st.subheader("Curvas de Força Trativa")
        show_jazar_image("jazar_accel_level.png", "Tractive Effort Diagram")
        
        # Gerar gráfico
        rpm = np.linspace(800, rpm_limit, 100)
        torque_motor = np.interp(rpm, [800, rpm_torque_max, rpm_power_max, rpm_limit], [torque_max*0.7, torque_max, torque_max*0.9, torque_max*0.6])
        df_traction = pd.DataFrame()
        Wf_flat, Wr_flat = vehicle.dynamic_loads(0, 0)
        F_limit_flat = vehicle.max_tractive_force(Wf_flat, Wr_flat, mu)

        for i, ratio in enumerate(gear_ratios):
            v_kmh = ((rpm * 2 * np.pi / 60) * tire_radius / (ratio * final_drive)) * 3.6
            ft = (torque_motor * ratio * final_drive * eta_d) / tire_radius
            ft = np.minimum(ft, F_limit_flat)
            df_g = pd.DataFrame({'Vel (km/h)': v_kmh, 'Força (N)': ft, 'Marcha': f"{i+1}ª"})
            df_traction = pd.concat([df_traction, df_g])
        
        st.altair_chart(alt.Chart(df_traction).mark_line().encode(
            x='Vel (km/h)', y='Força (N)', color='Marcha', tooltip=['Marcha', 'Vel (km/h)', 'Força (N)']
        ).interactive(), use_container_width=True)

# ==============================================================================
# MODO 2: PARADO (Plano e Inclinado)
# ==============================================================================
elif analysis_mode == "🅿️ Veículo Parado (Plano e Inclinado)":
    st.header("🅿️ Veículo Parado")

    tab_plano, tab_rampa = st.tabs(["Pista Plana (Cargas & Posição CG)", "Pista Inclinada (Limites)"])

    with tab_plano:
        st.subheader("Cargas Estáticas e Posição Lateral do CG")
        show_jazar_image("jazar_parked_level.png", "Parked Car on a Level Road")

        Wf = W * (c/L)
        Wr = W * (b/L)
        W_left = W * (0.5 + ty/t)
        W_right = W * (0.5 - ty/t)

        c1, c2 = st.columns(2)
        c1.metric("Eixo Dianteiro", f"{Wf:.1f} N", f"{(Wf/W)*100:.1f}%")
        c2.metric("Eixo Traseiro", f"{Wr:.1f} N", f"{(Wr/W)*100:.1f}%")
        
        st.divider()
        st.markdown("**Visualização da Distribuição Lateral:**")
        
        # Gráfico de barras simples para lateral
        df_lat = pd.DataFrame({
            'Lado': ['Esquerdo', 'Direito'],
            'Carga (N)': [W_left, W_right]
        })
        chart_lat = alt.Chart(df_lat).mark_bar().encode(
            x='Lado', y='Carga (N)', color='Lado', tooltip=['Lado', 'Carga (N)']
        ).properties(height=300)
        st.altair_chart(chart_lat, use_container_width=True)

    with tab_rampa:
        st.subheader("Análise de Estabilidade na Rampa")
        show_jazar_image("jazar_parked_grade.png", "Parked Car on an Inclined Road")

        theta = st.slider("Inclinação da Rampa (°)", 0.0, 60.0, 15.0)
        trad = np.radians(theta)
        
        Wf_inc = (W/L) * (c*np.cos(trad) - h*np.sin(trad))
        Wr_inc = (W/L) * (b*np.cos(trad) + h*np.sin(trad))
        
        lim_angle = np.degrees(np.arctan(c/h))
        
        k1, k2, k3 = st.columns(3)
        k1.metric("W Dianteiro", f"{Wf_inc:.0f} N")
        k2.metric("W Traseiro", f"{Wr_inc:.0f} N")
        k3.metric("Limite Tombamento", f"{lim_angle:.1f}°")

        if theta > lim_angle:
            st.error("⚠️ ÂNGULO CRÍTICO EXCEDIDO! O veículo tombaria para trás.")

        # --- GRÁFICO DE SENSIBILIDADE ---
        st.markdown("#### 📉 Gráfico: Cargas vs. Ângulo de Inclinação")
        st.caption("Observe como a carga no eixo dianteiro (azul) diminui até chegar a zero (ponto de tombamento).")
        
        angles = np.linspace(0, lim_angle + 10, 50) # Vai um pouco além do limite
        data_rampa = []
        for ang in angles:
            arad = np.radians(ang)
            wf_i = (W/L) * (c*np.cos(arad) - h*np.sin(arad))
            wr_i = (W/L) * (b*np.cos(arad) + h*np.sin(arad))
            # Trava em zero para gráfico ficar bonito
            if wf_i < 0: wf_i = 0
            
            data_rampa.append({'Ângulo (°)': ang, 'Carga (N)': wf_i, 'Eixo': 'Dianteiro'})
            data_rampa.append({'Ângulo (°)': ang, 'Carga (N)': wr_i, 'Eixo': 'Traseiro'})
        
        df_rampa = pd.DataFrame(data_rampa)
        
        chart_rampa = alt.Chart(df_rampa).mark_line().encode(
            x='Ângulo (°)',
            y='Carga (N)',
            color='Eixo',
            tooltip=['Ângulo (°)', 'Carga (N)', 'Eixo']
        ).interactive()
        
        # Adiciona linha vertical no ângulo atual
        rule = alt.Chart(pd.DataFrame({'x': [theta]})).mark_rule(color='red', strokeDash=[5,5]).encode(x='x')
        
        st.altair_chart(chart_rampa + rule, use_container_width=True)


# ==============================================================================
# MODO 3: CURVA (Banked Road)
# ==============================================================================
elif analysis_mode == "🔄 Veículo em Curva (Banked Road)":
    st.header("🔄 Veículo em Pista Lateralmente Inclinada")
    show_jazar_image("jazar_banked.png", "Parked Car on a Banked Road")
    
    phi = st.slider("Ângulo Superelevação ϕ (°)", 0.0, 45.0, 10.0)
    mu_lat = st.slider("Atrito Lateral", 0.1, 1.2, 0.8)
    prad = np.radians(phi)

    W_low = (W/t) * ((t/2)*np.cos(prad) + h*np.sin(prad))
    W_high = (W/t) * ((t/2)*np.cos(prad) - h*np.sin(prad))

    c1, c2 = st.columns(2)
    c1.metric("Rodas Baixas (Externas)", f"{W_low:.0f} N")
    c2.metric("Rodas Altas (Internas)", f"{W_high:.0f} N")

    # Limites
    lim_tomb = np.degrees(np.arctan(t/(2*h)))
    lim_slide = np.degrees(np.arctan(mu_lat))
    
    # --- GRÁFICO DE ESTABILIDADE LATERAL ---
    st.markdown("#### 📉 Gráfico: Estabilidade Lateral (Tombamento vs Deslizamento)")
    st.caption("O veículo perde estabilidade quando a linha da roda interna (alta) cruza o zero (tombamento) ou quando excede o atrito.")
    
    angles_lat = np.linspace(0, min(lim_tomb + 10, 60), 50)
    data_lat = []
    for ang in angles_lat:
        arad = np.radians(ang)
        w_l = (W/t) * ((t/2)*np.cos(arad) + h*np.sin(arad))
        w_h = (W/t) * ((t/2)*np.cos(arad) - h*np.sin(arad))
        if w_h < 0: w_h = 0
        data_lat.append({'Ângulo (°)': ang, 'Carga (N)': w_l, 'Roda': 'Externa (Baixa)'})
        data_lat.append({'Ângulo (°)': ang, 'Carga (N)': w_h, 'Roda': 'Interna (Alta)'})

    df_lat_chart = pd.DataFrame(data_lat)
    chart_lat_lines = alt.Chart(df_lat_chart).mark_line().encode(
        x='Ângulo (°)', y='Carga (N)', color='Roda'
    )
    
    # Regra do limite atual
    rule_lat = alt.Chart(pd.DataFrame({'x': [phi]})).mark_rule(color='red').encode(x='x')
    
    st.altair_chart(chart_lat_lines + rule_lat, use_container_width=True)
    
    l1, l2 = st.columns(2)
    l1.metric("Limite Tombamento", f"{lim_tomb:.1f}°")
    l2.metric("Limite Deslizamento", f"{lim_slide:.1f}°")

    if phi > lim_tomb: st.error("⚠️ TOMBAMENTO LATERAL!")

# ==============================================================================
# MODO 4: FRENAGEM
# ==============================================================================
elif analysis_mode == "🛑 Frenagem (Ideal e Eixo Simples)":
    st.header("🛑 Desaceleração e Freios")
    show_jazar_image("jazar_braking.png", "Braking Forces Diagram")

    col_in1, col_in2 = st.columns(2)
    mu_b = col_in1.slider("Atrito Pneu-Solo", 0.2, 1.0, 0.8)
    theta_b = col_in2.slider("Inclinação Pista (°)", -20.0, 20.0, 0.0)
    trad = np.radians(theta_b)

    dec_ideal = g * (mu_b * np.cos(trad) + np.sin(trad))
    
    # Travamento eixos
    den_f = 1 - mu_b * (h/L)
    den_r = 1 + mu_b * (h/L)
    dec_front = (g * (mu_b * (c/L)) / den_f) + g*np.sin(trad) if den_f > 0 else 0
    dec_rear = (g * (mu_b * (b/L)) / den_r) + g*np.sin(trad)

    c1, c2, c3 = st.columns(3)
    c1.metric("4 Rodas (Ideal)", f"{dec_ideal:.2f} m/s²")
    c2.metric("Só Dianteiro", f"{dec_front:.2f} m/s²")
    c3.metric("Só Traseiro", f"{dec_rear:.2f} m/s²")

    # --- GRÁFICO DE TRANSFERÊNCIA DE PESO NA FRENAGEM ---
    st.markdown("#### 📉 Gráfico: Transferência de Peso Dinâmica")
    st.caption("Conforme desaceleramos mais forte, o peso migra da traseira para a dianteira.")
    
    # Certifica que exista uma instância de Vehicle (é criada no modo de aceleração);
    # caso contrário, cria uma instância mínima para uso nos demais modos.
    try:
        vehicle
    except NameError:
        vehicle = Vehicle(M, L, b, c, h, Af, Cd, fr, 1.225, 'FWD (Tração Dianteira)', 0.30, [1.0], 4.0, 0.90)
    
    decel_range = np.linspace(0, dec_ideal, 20)
    data_brake = []
    for d in decel_range:
        # ax é negativo na frenagem para a fórmula dynamic_loads
        wf_b, wr_b = vehicle.dynamic_loads(-d, trad)
        data_brake.append({'Desaceleração (m/s²)': d, 'Carga (N)': wf_b, 'Eixo': 'Dianteiro'})
        data_brake.append({'Desaceleração (m/s²)': d, 'Carga (N)': wr_b, 'Eixo': 'Traseiro'})
    
    df_brake = pd.DataFrame(data_brake)
    chart_brake = alt.Chart(df_brake).mark_line().encode(
        x='Desaceleração (m/s²)', y='Carga (N)', color='Eixo'
    ).interactive()
    
    st.altair_chart(chart_brake, use_container_width=True)

# ==============================================================================
# MODO 5: TRAILER
# ==============================================================================
elif analysis_mode == "🚛 Veículo com Trailer (Inclinado)":
    st.header("🚛 Trailer em Via Inclinada")
    show_jazar_image("jazar_trailer.png", "Car with Trailer Diagram")
    
    col1, col2 = st.columns(2)
    with col1:
        Mt = st.number_input("Massa Trailer (kg)", 500.0)
        Wt = Mt * g
        Lt = st.number_input("Comp. Trailer (m)", 2.0)
        lt_cg = st.number_input("CG Trailer ao Eixo (m)", 0.2)
    with col2:
        lh = st.number_input("Engate ao Eixo Tras. Carro (m)", 0.8)
        theta_t = st.slider("Inclinação Rampa (°)", 0.0, 20.0, 5.0)
        trad = np.radians(theta_t)

    W_engate = (Wt * np.cos(trad)) * (lt_cg / Lt) 
    
    # Cargas originais (sem trailer) na rampa
    Wf_car = (W/L) * (c*np.cos(trad) - h*np.sin(trad))
    Wr_car = (W/L) * (b*np.cos(trad) + h*np.sin(trad))

    # Deltas
    dWf = - (W_engate * lh) / L
    dWr = W_engate * (1 + lh/L)

    Wf_final = Wf_car + dWf
    Wr_final = Wr_car + dWr
    
    st.metric("Carga Vertical Engate", f"{W_engate:.1f} N")

    # --- GRÁFICO COMPARATIVO COM/SEM TRAILER ---
    st.markdown("#### 📊 Comparativo: Efeito do Trailer nos Eixos")
    st.caption("Note o efeito 'gangorra': O trailer adiciona peso atrás, aliviando a frente e sobrecarregando a traseira.")

    data_trailer = [
        {'Eixo': 'Dianteiro', 'Condição': 'Sem Trailer', 'Carga (N)': Wf_car},
        {'Eixo': 'Dianteiro', 'Condição': 'Com Trailer', 'Carga (N)': Wf_final},
        {'Eixo': 'Traseiro', 'Condição': 'Sem Trailer', 'Carga (N)': Wr_car},
        {'Eixo': 'Traseiro', 'Condição': 'Com Trailer', 'Carga (N)': Wr_final},
    ]
    df_trailer = pd.DataFrame(data_trailer)
    
    chart_trailer = alt.Chart(df_trailer).mark_bar().encode(
        x=alt.X('Eixo', axis=None),
        y='Carga (N)',
        color='Condição',
        column='Eixo', # Agrupa por eixo
        tooltip=['Condição', 'Carga (N)']
    ).properties(width=150)
    
    st.altair_chart(chart_trailer, use_container_width=False)
    
    if Wf_final <= 0: st.error("🚨 PERIGO: Veículo Empinando!")

st.markdown("---")
st.caption("Simulador Atividade 02 - Engenharia Mecatrônica")