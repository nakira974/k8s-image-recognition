FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /app

ENV ASPNETCORE_ENVIRONMENT=Development
FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["ImageAnalyzerV1.csproj", "ImageAnalyzerV1/"]
RUN dotnet restore "ImageAnalyzerV1/ImageAnalyzerV1.csproj"
COPY . .
WORKDIR "/src/ImageAnalyzerV1"
RUN dotnet build "ImageAnalyzerV1.csproj" -c Debug -o /app/build

FROM build AS publish
RUN dotnet publish "ImageAnalyzerV1.csproj" -c Debug -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "ImageAnalyzerV1.dll"]
