program TesteProcedimento;

{ Recebe 2, Não retorna nada }
procedure ImprimeMaior(x, y: integer);
begin
    write('O maior numero entre ', x);
    write(' e ', y);
    write(' e: ');

    if x > y then
        writeln(x)
    else
        writeln(y);
end;

begin
    { Apenas empilha os argumentos e chama }
    ImprimeMaior(10, 20);
    writeln('Fim do teste.');
end.
