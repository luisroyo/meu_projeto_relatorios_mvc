// Tipos compartilhados entre serviços
export interface RondaEmAndamento {
    em_andamento: boolean;
    ronda?: {
        id: number;
        inicio?: string;
        data_plantao?: string;
        hora_entrada?: string;
        escala_plantao?: string;
        turno?: string;
        observacoes?: string;
        user_id?: number;
        user_nome?: string;
    };
}
