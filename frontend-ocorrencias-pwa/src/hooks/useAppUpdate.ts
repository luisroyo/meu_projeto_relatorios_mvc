import { useState, useEffect } from 'react';

interface UpdateInfo {
  hasUpdate: boolean;
  isUpdating: boolean;
  updateApp: () => void;
  forceUpdate: () => void;
}

export const useAppUpdate = (): UpdateInfo => {
  const [hasUpdate, setHasUpdate] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    // Registrar o Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);

          // Verificar atualizações mais frequentemente
          const checkForUpdates = () => {
            registration.update();
          };

          // Verificar a cada 2 minutos (mais agressivo)
          const interval = setInterval(checkForUpdates, 2 * 60 * 1000);

          // Listener para quando uma nova versão está disponível
          registration.addEventListener('updatefound', () => {
            console.log('Nova versão do app disponível!');
            setHasUpdate(true);
          });

          // Listener para quando o Service Worker é atualizado
          const handleControllerChange = () => {
            console.log('Service Worker atualizado!');
            setHasUpdate(false);
            setIsUpdating(false);
            // Recarregar a página para aplicar as atualizações
            window.location.reload();
          };

          // Listener para mensagens do Service Worker
          const handleMessage = (event: MessageEvent) => {
            console.log('Mensagem recebida do Service Worker:', event.data);
            if (event.data && event.data.type === 'UPDATE_READY') {
              console.log('Atualização pronta - recarregando...');
              setHasUpdate(false);
              setIsUpdating(false);
              window.location.reload();
            }
            if (event.data && event.data.type === 'FORCE_UPDATE_READY') {
              console.log('Força atualização pronta - recarregando...');
              setHasUpdate(false);
              setIsUpdating(false);
              window.location.reload();
            }
          };

          navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);
          navigator.serviceWorker.addEventListener('message', handleMessage);

          // Verificar se já há uma atualização pendente
          if (registration.waiting) {
            console.log('Atualização pendente encontrada!');
            setHasUpdate(true);
          }

          // Verificar atualizações na inicialização
          setTimeout(() => {
            registration.update();
          }, 1000);

          return () => {
            clearInterval(interval);
            navigator.serviceWorker.removeEventListener('controllerchange', handleControllerChange);
            navigator.serviceWorker.removeEventListener('message', handleMessage);
          };
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }
  }, []); // Remove isUpdating da dependência

  const updateApp = () => {
    console.log('Iniciando atualização...');
    setIsUpdating(true);

    // Esconder notificação imediatamente
    setHasUpdate(false);

    // Forçar atualização do Service Worker
    if ('serviceWorker' in navigator) {
      if (navigator.serviceWorker.controller) {
        // Se já temos um controller, envia mensagem para pular espera
        navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
        console.log('Mensagem SKIP_WAITING enviada');

        // Fallback: se não receber resposta em 3 segundos, recarrega
        setTimeout(() => {
          console.log('Fallback: timeout - recarregando página');
          window.location.reload();
        }, 3000);
      } else {
        // Fallback: recarrega a página diretamente
        console.log('Fallback: recarregando página diretamente');
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } else {
      // Fallback para navegadores sem Service Worker
      console.log('Fallback: navegador sem Service Worker');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  };

  const forceUpdate = () => {
    console.log('Forçando atualização completa...');
    setIsUpdating(true);
    setHasUpdate(false);

    // Limpar localStorage e sessionStorage
    try {
      localStorage.clear();
      sessionStorage.clear();
      console.log('Storage limpo');
    } catch (error) {
      console.log('Erro ao limpar storage:', error);
    }

    // Forçar atualização do Service Worker
    if ('serviceWorker' in navigator) {
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'FORCE_UPDATE' });
        console.log('Mensagem FORCE_UPDATE enviada');

        // Fallback: recarrega em 3 segundos
        setTimeout(() => {
          console.log('Fallback: recarregando página');
          window.location.reload();
        }, 3000);
      } else {
        // Fallback: recarrega diretamente
        console.log('Fallback: recarregando página diretamente');
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } else {
      // Fallback para navegadores sem Service Worker
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  };

  return {
    hasUpdate,
    isUpdating,
    updateApp,
    forceUpdate
  };
};
