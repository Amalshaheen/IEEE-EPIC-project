"""
Main CLI application for IEEE EPIC STT system using Typer.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path

from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine
from ieee_epic.core.ai_response import AIResponseSystem

app = typer.Typer(
    name="ieee-epic",
    help="IEEE EPIC Speech-to-Text System with AI Integration",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def status(
    config_file: str = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Show system status and available features."""
    settings = Settings.load_from_file(config_file) if config_file else Settings()
    
    # Create status table
    table = Table(title="IEEE EPIC STT System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    # Platform info
    platform_emoji = "🍓" if settings.system.is_raspberry_pi else "🖥️"
    table.add_row(
        "Platform", 
        f"{platform_emoji} {settings.system.platform or 'Unknown'}", 
        f"RPi: {settings.system.is_raspberry_pi}"
    )
    
    # STT Engine
    stt_engine = STTEngine(settings)
    stt_status = stt_engine.get_status()
    stt_emoji = "✅" if stt_status['ready'] else "❌"
    
    online_status = "🌐 Online" if settings.models.use_online_stt else "📴 Offline"
    backend_info = f"{settings.models.preferred_backend} ({online_status})"
    
    table.add_row(
        "STT Engine",
        f"{stt_emoji} {'Ready' if stt_status['ready'] else 'Not Ready'}",
        f"Backend: {backend_info}"
    )
    
    # Show available backends
    if stt_status['backends']:
        backends_str = ", ".join(stt_status['backends'])
        table.add_row(
            "Available Backends",
            "📋 Listed",
            backends_str
        )
    
    # Languages
    for lang in settings.models.supported_languages:
        available = settings.is_model_available(lang)
        lang_emoji = "✅" if available else "❌"
        lang_name = "English" if lang == "en" else "Malayalam"
        table.add_row(
            f"{lang_name} Model",
            f"{lang_emoji} {'Available' if available else 'Missing'}",
            str(settings.get_model_path(lang))
        )
    
    # AI System
    ai_system = AIResponseSystem(settings)
    ai_status = ai_system.get_status()
    ai_emoji = "✅" if ai_status['gemini_available'] else "⚠️"
    ai_status_text = "Gemini Connected" if ai_status['gemini_available'] else "API Key Missing"
    
    table.add_row(
        "AI Responses",
        f"{ai_emoji} {ai_status_text}",
        f"Model: {ai_status['model']}"
    )
    
    console.print(table)


@app.command()
def stt(
    language: str = typer.Option("auto", "--lang", "-l", help="Language (en/ml/auto)"),
    duration: float = typer.Option(5.0, "--duration", "-d", help="Recording duration"),
    config_file: str = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Run speech-to-text recognition."""
    settings = Settings.load_from_file(config_file) if config_file else Settings()
    settings.audio.duration = duration
    
    engine = STTEngine(settings)
    
    if not engine.is_ready():
        rprint("[red]❌ STT engine not ready. Please check your models.[/red]")
        raise typer.Exit(1)
    
    rprint(f"🎤 Starting STT recognition (Language: {language}, Duration: {duration}s)")
    rprint(f"Backend: {settings.models.preferred_backend} ({'online' if settings.models.use_online_stt else 'offline'})")
    
    try:
        results = engine.recognize_speech(language=language)
        
        if results:
            rprint("🎯 [green]Recognition Results:[/green]")
            for key, text in results.items():
                rprint(f"  [cyan]{key}:[/cyan] {text}")
            
            best_result = engine.get_best_result(results)
            if best_result:
                rprint(f"\n📝 [yellow]Best Result:[/yellow] {best_result}")
        else:
            rprint("[red]❌ No speech recognized[/red]")
            
    except KeyboardInterrupt:
        rprint("\n[yellow]Recognition cancelled[/yellow]")


@app.command()
def stream(
    language: str = typer.Option("auto", "--lang", "-l", help="Language (en/ml/auto)"),
    backend: str = typer.Option("deepgram", "--backend", "-b", help="STT backend (deepgram/auto)"),
    config_file: str = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Run real-time streaming speech recognition (requires Deepgram backend)."""
    settings = Settings.load_from_file(config_file) if config_file else Settings()
    
    # Enable online STT and set preferred backend
    settings.models.use_online_stt = True
    if backend == "auto":
        # Keep existing preferred backend
        pass
    else:
        settings.models.preferred_backend = backend
    
    engine = STTEngine(settings)
    
    if not engine.is_ready():
        rprint("[red]❌ STT engine not ready. Please check your models.[/red]")
        raise typer.Exit(1)
    
    if 'deepgram' not in engine.backends:
        rprint("[red]❌ Streaming requires Deepgram backend.[/red]")
        rprint("Please set DEEPGRAM_API_KEY environment variable and enable online STT.")
        rprint("Example: export DEEPGRAM_API_KEY=your_api_key")
        raise typer.Exit(1)
    
    rprint(f"🌊 [green]Starting streaming STT recognition with Deepgram[/green]")
    rprint(f"Language: {language} | Backend: {settings.models.preferred_backend}")
    rprint("Press Ctrl+C to stop | Speak into your microphone...")
    
    try:
        for transcript in engine.stream_recognize(language=language):
            if transcript.strip():
                rprint(f"📝 [cyan]{transcript}[/cyan]")
                
    except KeyboardInterrupt:
        rprint("\n[yellow]Streaming stopped by user[/yellow]")


@app.command()
def interactive():
    """Run interactive speech recognition mode."""
    settings = Settings()
    engine = STTEngine(settings)
    
    if not engine.is_ready():
        rprint("[red]❌ STT engine not ready. Please check your models.[/red]")
        raise typer.Exit(1)
    
    engine.interactive_mode()


@app.command()
def conversation(
    config_file: str = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """Run complete conversational AI assistant."""
    settings = Settings.load_from_file(config_file) if config_file else Settings()
    
    # Initialize systems
    stt_engine = STTEngine(settings)
    ai_system = AIResponseSystem(settings)
    
    if not stt_engine.is_ready():
        rprint("[red]❌ STT engine not ready. Please check your models.[/red]")
        raise typer.Exit(1)
    
    rprint("🤖 [green]IEEE EPIC Conversational AI Assistant[/green]")
    rprint("Commands: 'listen' (start listening), 'quit' (exit)")
    
    # Show status
    ai_status = ai_system.get_status()
    online_status = "✅ Gemini API" if ai_status['gemini_available'] else "⚠️ API Key Missing"
    rprint(f"AI Status: {online_status}")
    
    while True:
        try:
            command = typer.prompt("\n📝 Command").strip().lower()
            
            if command == 'quit':
                rprint("[yellow]👋 Goodbye![/yellow]")
                break
            elif command == 'listen':
                rprint("🎤 Listening... (speak now)")
                
                # Get speech input
                stt_results = stt_engine.recognize_speech(language="auto")
                
                if stt_results:
                    user_input = stt_engine.get_best_result(stt_results)
                    
                    if user_input:
                        rprint(f"👤 [cyan]You said:[/cyan] {user_input}")
                        
                        # Generate AI response
                        ai_response = ai_system.generate_response(user_input)
                        rprint(f"🤖 [green]AI Response:[/green] {ai_response}")
                    else:
                        rprint("[red]❌ Could not understand speech[/red]")
                else:
                    rprint("[red]❌ No speech detected[/red]")
            else:
                rprint("[red]❌ Unknown command. Use 'listen' or 'quit'[/red]")
                
        except KeyboardInterrupt:
            rprint("\n[yellow]👋 Goodbye![/yellow]")
            break
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")


@app.command()
def demo():
    """Run AI response demo with text input."""
    settings = Settings()
    ai_system = AIResponseSystem(settings)
    
    rprint("🧪 [green]AI Response Demo[/green]")
    ai_system.interactive_demo()


@app.command()
def setup(
    force: bool = typer.Option(False, "--force", help="Force setup even if models exist")
):
    """Setup models and configuration."""
    from ieee_epic.utils.setup import SetupManager
    
    settings = Settings()
    setup_manager = SetupManager(settings)
    
    rprint("🔧 [green]IEEE EPIC STT Setup[/green]")
    
    if setup_manager.run_setup(force=force):
        rprint("[green]✅ Setup completed successfully![/green]")
    else:
        rprint("[red]❌ Setup failed. Please check the logs.[/red]")
        raise typer.Exit(1)


@app.command()
def configure_online(
    provider: str = typer.Option("deepgram", "--provider", "-p", help="Online STT provider (deepgram)"),
    api_key: str = typer.Option(None, "--api-key", help="API key for the provider"),
    save_config: bool = typer.Option(True, "--save/--no-save", help="Save configuration to file")
):
    """Configure online STT services (Deepgram)."""
    rprint("🌐 [green]Online STT Configuration[/green]")
    
    if provider not in ["deepgram"]:
        rprint(f"[red]❌ Unsupported provider: {provider}[/red]")
        rprint("Supported providers: deepgram")
        raise typer.Exit(1)
    
    # Get API key if not provided
    if not api_key:
        if provider == "deepgram":
            rprint("🔑 Deepgram API Key Required")
            rprint("Get your free API key from: https://console.deepgram.com/")
            api_key = typer.prompt("Enter your Deepgram API key", hide_input=True)
    
    # Create settings with online STT enabled
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = provider
    
    if provider == "deepgram":
        settings.models.deepgram_api_key = api_key
        settings.models.deepgram_model = "nova-2"
        settings.models.deepgram_language = "en-US"
        settings.models.enable_streaming = True
    
    # Test the configuration
    rprint("🧪 Testing configuration...")
    try:
        engine = STTEngine(settings)
        
        if provider in engine.backends:
            rprint(f"[green]✅ {provider.title()} backend initialized successfully![/green]")
            
            # Show environment variable setup
            if provider == "deepgram":
                rprint("\n📋 [yellow]Environment Variable Setup:[/yellow]")
                rprint(f"export DEEPGRAM_API_KEY='{api_key}'")
                rprint("\nAdd this to your ~/.bashrc or ~/.zshrc for persistence.")
            
            # Save configuration if requested
            if save_config:
                config_path = Path("ieee_epic_config.json")
                # Don't save API keys to config files for security
                settings.models.deepgram_api_key = None
                
                if settings.save_to_file(config_path):
                    rprint(f"[green]✅ Configuration saved to {config_path}[/green]")
                    rprint("[yellow]Note: API keys are not saved to config files for security.[/yellow]")
                    rprint("Use environment variables for API keys.")
            
        else:
            rprint(f"[red]❌ Failed to initialize {provider} backend[/red]")
            rprint("Check your API key and internet connection.")
            raise typer.Exit(1)
            
    except Exception as e:
        rprint(f"[red]❌ Configuration test failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()