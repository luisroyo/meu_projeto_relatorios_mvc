import React from 'react';
import { Input } from '../Input';
import { AutoComplete } from '../AutoComplete';
import { colors } from '../../theme/colors';
import { buscarCondominios } from '../../services/domains/condominios';

interface RondaConfiguracoesProps {
    dataPlantao: string;
    setDataPlantao: (data: string) => void;
    escalaPlantao: string;
    setEscalaPlantao: (escala: string) => void;
    condominioNome: string;
    setCondominioNome: (nome: string) => void;
    setCondominioId: (id: number) => void;
    setResidencial: (residencial: string) => void;
    buscarRondasDoCondominio: (id: number) => Promise<void>;
    periodoInicio: string;
    periodoFim: string;
    condominiosPendentes: string[];
    token: string;
}

export const RondaConfiguracoes: React.FC<RondaConfiguracoesProps> = ({
    dataPlantao,
    setDataPlantao,
    escalaPlantao,
    setEscalaPlantao,
    condominioNome,
    setCondominioNome,
    setCondominioId,
    setResidencial,
    buscarRondasDoCondominio,
    periodoInicio,
    periodoFim,
    condominiosPendentes,
    token
}) => {
    const calcularPeriodoFormatado = () => {
        if (!periodoInicio || !periodoFim) return '';
        
        const inicio = new Date(periodoInicio);
        const fim = new Date(periodoFim);
        
        return `${inicio.toLocaleString('pt-BR')} - ${fim.toLocaleString('pt-BR')}`;
    };

    return (
        <div style={{
            backgroundColor: colors.surface,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <h3 style={{ margin: '0 0 20px 0', color: colors.headingText }}>
                ⚙️ Configurações do Plantão
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Data do Plantão
                    </label>
                    <Input
                        type="date"
                        value={dataPlantao}
                        onChange={(e) => setDataPlantao(e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Escala do Plantão
                    </label>
                    <select
                        value={escalaPlantao}
                        onChange={(e) => setEscalaPlantao(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '10px',
                            border: '2px solid #007bff',
                            borderRadius: '4px',
                            fontSize: '16px'
                        }}
                    >
                        <option value="06 às 18">06 às 18</option>
                        <option value="18 às 06">18 às 06</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Condomínio
                    </label>
                    <AutoComplete
                        placeholder="Digite o nome do condomínio"
                        value={condominioNome}
                        onChange={setCondominioNome}
                        onSelect={(condominio) => {
                            console.log('Condomínio selecionado:', condominio);
                            setCondominioId(condominio.id);
                            setCondominioNome(condominio.nome);
                            setResidencial(condominio.nome);
                            buscarRondasDoCondominio(condominio.id);
                        }}
                        searchFunction={async (query: string) => {
                            try {
                                const response = await buscarCondominios(query, token);
                                return response.condominios || [];
                            } catch (error) {
                                console.error('Erro ao buscar condomínios:', error);
                                return [];
                            }
                        }}
                        displayField="nome"
                        token={token}
                        style={{
                            backgroundColor: '#FFFFFF',
                            color: '#000000',
                            border: '2px solid #007bff'
                        }}
                    />
                </div>
            </div>

            {/* Período Calculado */}
            {dataPlantao && escalaPlantao && (
                <div style={{
                    marginTop: '15px',
                    padding: '15px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '4px',
                    border: '1px solid #dee2e6'
                }}>
                    <strong>📅 Período do Plantão:</strong>
                    <br />
                    {calcularPeriodoFormatado()}
                </div>
            )}

            {/* Condomínios Pendentes */}
            {condominiosPendentes.length > 0 && (
                <div style={{
                    marginTop: '15px',
                    padding: '15px',
                    backgroundColor: '#fff3cd',
                    borderRadius: '4px',
                    border: '1px solid #ffeaa7'
                }}>
                    <strong>⚠️ Condomínios Pendentes:</strong>
                    <br />
                    {condominiosPendentes.join(', ')}
                </div>
            )}
        </div>
    );
}; 