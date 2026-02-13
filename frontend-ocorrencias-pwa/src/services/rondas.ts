// Função utilitária para exportar relatório de rondas esporádicas no formato WhatsApp
export function gerarRelatorioRondasWhatsApp({ data_plantao, residencial, rondas }: {
    data_plantao: string;
    residencial: string;
    rondas: Array<{ inicio: string; termino: string; duracao: number; }>;
}): string {
    // Formatar data do plantão
    const data = new Date(data_plantao);
    const dataFormatada = data.toLocaleDateString('pt-BR');

    // Gerar relatório no formato especificado
    let relatorio = `Plantão ${dataFormatada} (18h às 06h)\n`;
    relatorio += `Residencial: ${residencial}\n\n`;

    rondas.forEach((ronda) => {
        relatorio += `\tInício: ${ronda.inicio}  – Término: ${ronda.termino} (${ronda.duracao} min)\n`;
    });

    relatorio += `\n✅ Total: ${rondas.length} rondas completas no plantão`;
    return relatorio;
}