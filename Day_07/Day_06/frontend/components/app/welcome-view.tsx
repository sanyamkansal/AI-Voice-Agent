import { Button } from '@/components/ui/button';
import { Storefront } from '@phosphor-icons/react/dist/ssr';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  isCallEnded?: boolean;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  isCallEnded,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="relative flex h-full w-full items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-500/20 via-background to-background">
      {/* Decorative background blur blobs */}
      <div className="absolute top-1/4 left-1/4 h-64 w-64 rounded-full bg-orange-500/10 blur-[100px]" />
      <div className="absolute bottom-1/4 right-1/4 h-64 w-64 rounded-full bg-yellow-500/10 blur-[100px]" />

      <section className="relative z-10 flex flex-col items-center justify-center text-center bg-background/40 backdrop-blur-xl border border-white/10 dark:border-white/5 shadow-2xl rounded-3xl p-10 md:p-14 max-w-lg mx-4">
        <div className="flex items-center justify-center mb-6 text-orange-500 drop-shadow-[0_0_15px_rgba(249,115,22,0.5)] transition-transform duration-500 hover:scale-110">
          <Storefront weight="duotone" size={96} />
        </div>

        <h1 className="text-foreground text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
          {isCallEnded ? 'Call Ended' : 'Dukaan Sathi'}
        </h1>
        
        <p className="text-muted-foreground max-w-prose leading-relaxed font-medium mb-8">
          {isCallEnded ? 'The conversation is over. Click below to start again!' : 'Ready to help you! Click the button below to start talking to your local shopkeeper assistant.'}
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="w-full sm:w-72 h-14 rounded-full font-mono text-sm font-bold tracking-wider uppercase bg-orange-500 hover:bg-orange-600 text-white shadow-[0_0_20px_rgba(249,115,22,0.4)] hover:shadow-[0_0_30px_rgba(249,115,22,0.6)] transition-all duration-300"
        >
          {isCallEnded ? 'Start New Call' : startButtonText}
        </Button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Built with LiveKit and Murf AI for the Voice for Bharat Challenge
        </p>
      </div>
    </div>
  );
};
