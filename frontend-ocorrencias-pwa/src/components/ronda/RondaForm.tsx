import React from 'react';
import { Button } from '../Button';
import { Input } from '../Input';
import { AutoComplete } from '../AutoComplete';
import { colors } from '../../theme/colors';
import { buscarCondominios } from '../../services/domains/condominios';

interface RondaFormProps {
    condominioNome: string;
    setCondominioNome: (nome: string) => void;
    setCondominioId: (id: number) => void;
    setResidencial: (residencial: string) => void;
    buscarRondasDoCondominio: (id: number) => Promise<void>;
    inicioRonda: string;
    setInicioRonda: (inicio: string) => void;
    residencial: string;
    loading: boolean;
    onIniciarRonda: () => void;
    token: string;
}

export const RondaForm: React.FC<RondaFormProps> = ({
    condominioNome,
    setCondominioNome,
    setCondominioId,
    setResidencial,
    buscarRondasDoCondominio,
    inicioRonda,
    setInicioRonda,
    residencial,
    loading,
    onIniciarRonda,
    token
}) => {
    return (
        <div style={{
            backgroundColor: colors.surface,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <h3 style={{ margin: '0 0 20px 0', color: colors.headingText }}>
                🚀 Nova Ronda
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginBottom: '20px' }}>
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

                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Horário de Início
                    </label>
                    <Input
                        type="time"
                        value={inicioRonda}
                        onChange={(e) => setInicioRonda(e.target.value)}
                    />
                </div>
            </div>

            <Button
                title="▶️ Iniciar Ronda"
                onClick={onIniciarRonda}
                disabled={loading || !residencial || !inicioRonda}
                style={{ backgroundColor: colors.success, marginRight: '10px' }}
            />
        </div>
    );
}; 