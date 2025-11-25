import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Simulador Dinâmica Veicular - Jazar", layout="wide")

st.title("🚗 Simulador de Dinâmica Veicular (Jazar - Cap. 2)")
st.subheader("Análise do Chevrolet Onix Plus 2026")
st.markdown("""
            **Trabalho 02 - Dinâmica Longitudinal**
            **Integrantes do Grupo:**
            - Gabriel Monteiro
            - Lucas Sander Guimarães Silva
            - Michael Yoshiaki Todoroki

            Esta ferramenta simula as reações nos pneus baseada nas equações de *Reza N. Jazar*.
            Use o menu lateral para configurar o veículo e as abas abaixo para ver os cenários.

            A configuração default é baseada no Chevrolet Onix Plus 2026.
            """)

# ==========================================
# 2. CLASSE DO VEÍCULO
# ==========================================
class Veiculo:
    def __init__(self, m, l, h, w, dist_front_pct):
        self.m = m              # Massa (kg)
        self.g = 9.81           # Gravidade
        self.L = l              # Entre-eixos (m)
        self.h = h              # Altura CG (m)
        self.w = w              # Bitola (m)
        
        # Define a1 e a2 com base na % de peso na frente
        self.a2 = (dist_front_pct / 100.0) * self.L # Distância CG ao eixo Traseiro
        self.a1 = self.L - self.a2                  # Distância CG ao eixo Dianteiro

    def get_loads_longitudinal(self, ax, angulo_graus):
        """Calcula cargas verticais considerando rampa e aceleração"""
        phi = np.radians(angulo_graus)
        W = self.m * self.g
        
        # Termo Estático/Rampa (Jazar 2.2)
        term_front_stat = 0.5 * W * ( (self.a2 / self.L) * np.cos(phi) - (self.h / self.L) * np.sin(phi) )
        term_rear_stat  = 0.5 * W * ( (self.a1 / self.L) * np.cos(phi) + (self.h / self.L) * np.sin(phi) )
        
        # Termo Dinâmico (Transferência de carga - Jazar 2.3/2.4)
        transf = 0.5 * self.m * ax * (self.h / self.L)
        
        Fz1 = term_front_stat - transf
        Fz2 = term_rear_stat + transf
        
        return max(0, Fz1), max(0, Fz2) # Evita força negativa (roda levantou)

    def get_loads_lateral(self, angulo_bank):
        """Calcula cargas laterais em pista inclinada (banked road)"""
        phi = np.radians(angulo_bank)
        W = self.m * self.g
        b1 = self.w / 2
        b2 = self.w / 2
        
        # Fz_in (lado de dentro/baixo), Fz_out (lado de fora/cima)
        # Jazar Seção 2.5
        Fz_baixo = 0.5 * (W / self.w) * (b2 * np.cos(phi) + self.h * np.sin(phi))
        Fz_cima  = 0.5 * (W / self.w) * (b1 * np.cos(phi) - self.h * np.sin(phi))
        
        return max(0, Fz_baixo), max(0, Fz_cima)

# ==========================================
# 3. SIDEBAR - INPUTS DO VEÍCULO
# ==========================================
st.sidebar.header("⚙️ Dados do Veículo")

# Valores Default do Onix Plus 2026
m_input = st.sidebar.number_input("Massa (kg)", value=1117.0, step=10.0)
l_input = st.sidebar.number_input("Entre-eixos (m)", value=2.60, step=0.01)
h_input = st.sidebar.number_input("Altura do CG (m)", value=0.54, step=0.01, help="Valor estimado para sedãs")
w_input = st.sidebar.number_input("Bitola (m)", value=1.508, step=0.01)
dist_input = st.sidebar.slider("Distribuição de Peso na Frente (%)", 40, 70, 60)

carro = Veiculo(m_input, l_input, h_input, w_input, dist_input)

# Mostra cálculo de a1 e a2
st.sidebar.markdown(f"""
---
**Cálculos Geométricos:**
* $a_1$ (CG à Frente): {carro.a1:.2f} m
* $a_2$ (CG à Trás): {carro.a2:.2f} m
""")

# ==========================================
# 4. ÁREA PRINCIPAL - ABAS
# ==========================================
tab1, tab2, tab3 = st.tabs(["⛰️ Rampa (Inclinado)", "🚀 Aceleração Longitudinal", "🏎️ Inclinação Lateral (Banked)"])

# --- TAB 1: RAMPA (MODELO B) ---
with tab1:
    st.header("Veículo em Rampa (Estático)")
    st.markdown("Analisa como o peso se desloca para o eixo traseiro conforme a inclinação da subida aumenta.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        angle_input = st.slider("Ângulo da Rampa (graus)", 0, 45, 0)
        fz1, fz2 = carro.get_loads_longitudinal(0, angle_input)
        
        st.metric("Carga Eixo Dianteiro (Fz1)", f"{fz1:.1f} N", delta=f"{fz1 - (carro.m*9.81*0.5*carro.a2/carro.L):.1f} N")
        st.metric("Carga Eixo Traseiro (Fz2)", f"{fz2:.1f} N", delta=f"{fz2 - (carro.m*9.81*0.5*carro.a1/carro.L):.1f} N")
    
    with col2:
        # Gráfico Variando o Ângulo
        angles = np.linspace(0, 45, 50)
        res_fz1 = []
        res_fz2 = []
        for a in angles:
            f1, f2 = carro.get_loads_longitudinal(0, a)
            res_fz1.append(f1)
            res_fz2.append(f2)
            
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(angles, res_fz1, label='Dianteiro (Fz1)', color='blue')
        ax.plot(angles, res_fz2, label='Traseiro (Fz2)', color='red')
        
        # Ponto atual
        ax.scatter([angle_input], [fz1], color='blue', s=100, zorder=5)
        ax.scatter([angle_input], [fz2], color='red', s=100, zorder=5)
        
        ax.set_title("Distribuição de Carga vs Ângulo da Rampa")
        ax.set_xlabel("Ângulo (graus)")
        ax.set_ylabel("Força Normal (N)")
        ax.grid(True, linestyle='--')
        ax.legend()
        st.pyplot(fig)

# --- TAB 2: ACELERAÇÃO (MODELO C e D) ---
with tab2:
    st.header("Aceleração Longitudinal")
    st.markdown("Simula a 'empinada' do carro. Analise a transferência de carga da frente para trás ao acelerar.")
    
    col_a1, col_a2 = st.columns([1, 2])
    
    with col_a1:
        accel_input = st.slider("Aceleração ($m/s^2$)", 0.0, 10.0, 2.0, step=0.1)
        ramp_accel = st.checkbox("Incluir Rampa na Simulação?", value=False)
        angle_accel = 0
        if ramp_accel:
            angle_accel = st.number_input("Ângulo da Rampa", 0, 30, 5)
            
        fz1_a, fz2_a = carro.get_loads_longitudinal(accel_input, angle_accel)
        
        st.warning(f"Total Fz: {(fz1_a + fz2_a)*2:.1f} N (Check de Massa)")
        
        if fz1_a <= 0:
            st.error("🚨 ALERTA: As rodas dianteiras perderam contato (Empinou!)")
    
    with col_a2:
        accels = np.linspace(0, 10, 50)
        res_fz1_a = []
        res_fz2_a = []
        
        for ac in accels:
            f1, f2 = carro.get_loads_longitudinal(ac, angle_accel)
            res_fz1_a.append(f1)
            res_fz2_a.append(f2)
            
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.plot(accels, res_fz1_a, label='Dianteiro (Fz1)', color='blue')
        ax2.plot(accels, res_fz2_a, label='Traseiro (Fz2)', color='red')
        
        # Linha de limite (zero)
        ax2.axhline(0, color='black', linewidth=1)
        
        # Ponto atual
        ax2.scatter([accel_input], [fz1_a], color='blue', s=100)
        ax2.scatter([accel_input], [fz2_a], color='red', s=100)

        ax2.set_title(f"Aceleração em Pista {'Plana' if angle_accel==0 else f'Inclinada ({angle_accel}°)'}")
        ax2.set_xlabel("Aceleração ($m/s^2$)")
        ax2.set_ylabel("Força Normal (N)")
        ax2.grid(True, linestyle='--')
        ax2.legend()
        st.pyplot(fig2)

# --- TAB 3: LATERAL (MODELO E) ---
with tab3:
    st.header("Inclinação Lateral (Banked Road)")
    st.markdown("Veículo parado ou em baixa velocidade numa pista com inclinação lateral (perfil de estrada).")
    
    bank_input = st.slider("Ângulo Lateral (Bank) - Graus", 0, 60, 0)
    
    fz_low, fz_high = carro.get_loads_lateral(bank_input)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1, 2])
    
    with col_l1:
        st.metric("Pneus de Baixo (Lado da queda)", f"{fz_low:.1f} N")
    with col_l2:
        st.metric("Pneus de Cima", f"{fz_high:.1f} N")
        if fz_high <= 0:
            st.error("🚨 TOMBAMENTO!")
            
    with col_l3:
        # Visualização em Barras é melhor aqui
        fig3, ax3 = plt.subplots(figsize=(5, 3))
        ax3.bar(["Lado Baixo", "Lado Cima"], [fz_low, fz_high], color=['green', 'orange'])
        ax3.set_title("Carga nos Pneus (Lateral)")
        ax3.set_ylabel("Força (N)")
        st.pyplot(fig3)