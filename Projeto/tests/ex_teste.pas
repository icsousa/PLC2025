program TesteFuncao;

var
    resultado: integer;

{ Recebe 2, Retorna 1 }
function CalculaDobroSoma(a, b: integer): integer;
begin

    CalculaDobroSoma := (a + b) * 2;
end;

begin
    writeln('A calcular (10 + 5) * 2...');
    resultado := CalculaDobroSoma(10, 5);
    writeln('Resultado obtido: ', resultado);
end.
