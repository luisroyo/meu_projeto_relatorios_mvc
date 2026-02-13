import React from 'react';
import { Button } from '../Button';
import { Input } from '../Input';
import { colors } from '../../theme/colors';

interface RondaControlesProps {
    rondaAtiva: any;
    tipoRonda: 'regular' | 'esporadica';
    logBruto: string;
    setLogBruto: (log: string) => void;
    horaSaida: string;
    setHoraSaida: (hora: string) => void;
    observacoes: string;
    setObservacoes: (obs: string) => void;
    onIniciarRonda: () => void;
    onFinalizarRonda: () => void;
    onGerarRelatorio: () => void;
    onEnviarWhatsApp: () => void;
    loading: boolean;
}

export const RondaControles: React.FC<RondaControlesProps> = ({
    rondaAtiva,
    tipoRonda,
    logBruto,
    setLogBruto,
    horaSaida,
    setHoraSaida,
    observacoes,
    setObservacoes,
    onIniciarRonda,
    onFinalizarRonda,
    onGerarRelatorio,
    onEnviarWhatsApp,
    loading
}) => {
    return (
        <div style={{
            backgroundColor: '#f8f9fa',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px'
        }}>
            <h3 style={{
                color: colors.primaryBg,
                marginBottom: '16px',
                fontSize: '18px',
                fontWeight: 'bold'
            }}>
                🎮 Controles
            </h3>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
                <Button
                    title="🚀 Iniciar Ronda"
                    onClick={onIniciarRonda}
                    disabled={loading || (rondaAtiva?.em_andamento || false)}
                    style={{ minWidth: '140px' }}
                />
                <Button
                    title="⏹️ Finalizar Ronda"
                    onClick={onFinalizarRonda}
                    disabled={loading || !(rondaAtiva?.em_andamento || false)}
                    variant="danger"
                    style={{ minWidth: '140px' }}
                />
                <Button
                    title="📄 Gerar Relatório"
                    onClick={onGerarRelatorio}
                    disabled={loading}
                    variant="secondary"
                    style={{ minWidth: '140px' }}
                />
                <Button
                    title="📱 Enviar WhatsApp"
                    onClick={onEnviarWhatsApp}
                    disabled={loading}
                    variant="success"
                    style={{ minWidth: '140px' }}
                />
            </div>

            {/* Campos para finalização */}
            {rondaAtiva?.em_andamento && (
                <div style={{
                    backgroundColor: '#fff',
                    padding: '16px',
                    borderRadius: '6px',
                    border: '1px solid #dee2e6'
                }}>
                    <h4 style={{
                        color: colors.primaryBg,
                        marginBottom: '12px',
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }}>
                        📝 Dados para Finalização
                    </h4>

                    {tipoRonda === 'regular' && (
                        <div style={{ marginBottom: '12px' }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                                Log Bruto
                            </label>
                            <textarea
                                value={logBruto}
                                onChange={(e) => setLogBruto(e.target.value)}
                                placeholder="Descreva as atividades realizadas..."
                                style={{
                                    width: '100%',
                                    minHeight: '80px',
                                    padding: '8px',
                                    border: '1px solid #ced4da',
                                    borderRadius: '4px',
                                    resize: 'vertical'
                                }}
                            />
                        </div>
                    )}

                    {tipoRonda === 'esporadica' && (
                        <div style={{ marginBottom: '12px' }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                                Hora de Saída
                            </label>
                            <Input
                                type="time"
                                value={horaSaida}
                                onChange={(e) => setHoraSaida(e.target.value)}
                            />
                        </div>
                    )}

                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                            Observações
                        </label>
                        <textarea
                            value={observacoes}
                            onChange={(e) => setObservacoes(e.target.value)}
                            placeholder="Observações adicionais..."
                            style={{
                                width: '100%',
                                minHeight: '60px',
                                padding: '8px',
                                border: '1px solid #ced4da',
                                borderRadius: '4px',
                                resize: 'vertical'
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}; 