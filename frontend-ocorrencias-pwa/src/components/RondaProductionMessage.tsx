import React from 'react';
import { BaseScreen } from './BaseScreen';
import { Button } from './Button';

export const RondaProductionMessage: React.FC = () => {
    return (
        <BaseScreen title="Controle de Rondas" subtitle="Funcionalidade em Desenvolvimento">
            <div style={{
                padding: '40px 20px',
                textAlign: 'center',
                maxWidth: '600px',
                margin: '0 auto'
            }}>
                <div style={{
                    backgroundColor: '#fff3cd',
                    border: '1px solid #ffeaa7',
                    borderRadius: '8px',
                    padding: '30px',
                    marginBottom: '20px'
                }}>
                    <h2 style={{
                        color: '#856404',
                        marginBottom: '20px',
                        fontSize: '24px'
                    }}>
                        🚧 Funcionalidade em Teste
                    </h2>

                    <p style={{
                        color: '#856404',
                        fontSize: '16px',
                        lineHeight: '1.6',
                        marginBottom: '20px'
                    }}>
                        A página de <strong>Controle de Rondas</strong> ainda está em desenvolvimento e testes.
                    </p>

                    <p style={{
                        color: '#856404',
                        fontSize: '16px',
                        lineHeight: '1.6',
                        marginBottom: '30px'
                    }}>
                        Em breve teremos novidades! Esta funcionalidade incluirá:
                    </p>

                    <div style={{
                        textAlign: 'left',
                        backgroundColor: '#fff',
                        padding: '20px',
                        borderRadius: '6px',
                        border: '1px solid #e9ecef'
                    }}>
                        <ul style={{
                            color: '#495057',
                            fontSize: '14px',
                            lineHeight: '1.8',
                            margin: '0',
                            paddingLeft: '20px'
                        }}>
                            <li>🎯 <strong>Rondas Regulares:</strong> Controle de plantões diários</li>
                            <li>⏰ <strong>Rondas Esporádicas:</strong> Registro de rondas pontuais</li>
                            <li>📊 <strong>Consolidação:</strong> Relatórios consolidados por turno</li>
                            <li>📱 <strong>WhatsApp:</strong> Envio automático de relatórios</li>
                            <li>📈 <strong>Estatísticas:</strong> Análise de performance</li>
                            <li>✅ <strong>Validações:</strong> Controle de horários e permissões</li>
                        </ul>
                    </div>

                    <div style={{
                        marginTop: '30px',
                        padding: '15px',
                        backgroundColor: '#d4edda',
                        border: '1px solid #c3e6cb',
                        borderRadius: '6px'
                    }}>
                        <p style={{
                            color: '#155724',
                            fontSize: '14px',
                            margin: '0'
                        }}>
                            <strong>💡 Dica:</strong> Para testar esta funcionalidade, acesse a aplicação em ambiente de desenvolvimento (localhost).
                        </p>
                    </div>
                </div>

                <Button
                    title="🔙 Voltar ao Menu Principal"
                    onClick={() => window.history.back()}
                    variant="secondary"
                    style={{ marginTop: '20px' }}
                />
            </div>
        </BaseScreen>
    );
}; 