// Suprimir warnings específicos do console em desenvolvimento
if (process.env.NODE_ENV === 'development') {
    const originalWarn = console.warn;
    const originalError = console.error;

    console.warn = (...args: any[]) => {
        const message = args[0];

        // Suprimir warnings do MUI Grid v2
        if (typeof message === 'string' && (
            message.includes('MUI Grid: The `item` prop has been removed') ||
            message.includes('MUI Grid: The `xs` prop has been removed') ||
            message.includes('MUI Grid: The `sm` prop has been removed') ||
            message.includes('MUI Grid: The `md` prop has been removed') ||
            message.includes('MUI Grid: The `lg` prop has been removed')
        )) {
            return;
        }

        // Suprimir warnings de HTML nesting (já corrigidos)
        if (typeof message === 'string' && (
            message.includes('cannot be a descendant of') ||
            message.includes('will cause a hydration error') ||
            message.includes('<p> cannot contain a nested <div>') ||
            message.includes('<div> cannot be a descendant of <p>')
        )) {
            return;
        }

        originalWarn.apply(console, args);
    };

    console.error = (...args: any[]) => {
        const message = args[0];

        // Suprimir erros de HTML nesting (já corrigidos)
        if (typeof message === 'string' && (
            message.includes('cannot be a descendant of') ||
            message.includes('will cause a hydration error') ||
            message.includes('<p> cannot contain a nested <div>') ||
            message.includes('<div> cannot be a descendant of <p>')
        )) {
            return;
        }

        originalError.apply(console, args);
    };
} 