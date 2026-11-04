import java.nio.file.*;
import java.util.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

/** Exploration exhaustive des marquages d'un reseau P/T PNML, sans bibliotheque externe. */
public final class PetriExplorer {
    record Step(List<Integer> previous, String transition) {}
    static int number(Element element, String tag, int fallback) {
        NodeList found = element.getElementsByTagName(tag);
        if (found.getLength() == 0) return fallback;
        Element container = (Element) found.item(0);
        NodeList text = container.getElementsByTagName("text");
        if (text.getLength() == 0) text = container.getElementsByTagName("value");
        String value = text.item(0).getTextContent().strip();
        return Integer.parseInt(value.substring(value.lastIndexOf(',') + 1));
    }
    public static void main(String[] args) throws Exception {
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        var xml = factory.newDocumentBuilder().parse(Path.of(args[0]).toFile());
        NodeList places = xml.getElementsByTagName("place"), transitions = xml.getElementsByTagName("transition");
        Map<String,Integer> pi = new LinkedHashMap<>(), ti = new LinkedHashMap<>();
        List<String> transitionNames = new ArrayList<>();
        List<Integer> initial = new ArrayList<>();
        for (int i=0;i<places.getLength();i++) {
            Element place=(Element)places.item(i);
            pi.put(place.getAttribute("id"),i);
            initial.add(number(place,"initialMarking",0));
        }
        for (int i=0;i<transitions.getLength();i++) {
            String id=((Element)transitions.item(i)).getAttribute("id");
            ti.put(id,i);transitionNames.add(id);
        }
        int[][] pre=new int[ti.size()][pi.size()],post=new int[ti.size()][pi.size()];
        NodeList arcs=xml.getElementsByTagName("arc");
        for (int i=0;i<arcs.getLength();i++) {
            Element arc=(Element)arcs.item(i);
            String from=arc.getAttribute("source"),to=arc.getAttribute("target");
            int weight=number(arc,"inscription",1);
            if(pi.containsKey(from) && ti.containsKey(to)) pre[ti.get(to)][pi.get(from)]+=weight;
            else if(ti.containsKey(from) && pi.containsKey(to)) post[ti.get(from)][pi.get(to)]+=weight;
            else throw new IllegalArgumentException("Arc non biparti : "+from+" -> "+to);
        }
        var start=List.copyOf(initial);
        Map<List<Integer>,Step> previous=new LinkedHashMap<>();
        previous.put(start,null);
        var queue=new ArrayDeque<List<Integer>>();queue.add(start);
        List<Integer> bad=null;int deadlocks=0,maxToken=0;boolean conserved=true;
        while(!queue.isEmpty()) {
            List<Integer> marking=queue.remove();
            int ca=marking.get(pi.get("ConfA")),cb=marking.get(pi.get("ConfB"));
            int free=marking.get(pi.get("Libre")),busy=marking.get(pi.get("Occupee"));
            boolean local=free+busy==1 && busy==ca+cb;
            for(String user:List.of("A","B")) local &=
                marking.get(pi.get("Attente"+user))+marking.get(pi.get("Conf"+user))
                +marking.get(pi.get("Refus"+user))+marking.get(pi.get("Annulee"+user))==1;
            conserved &= local;
            if(ca+cb>1 && bad==null)bad=marking;
            for(int tokens:marking)maxToken=Math.max(maxToken,tokens);
            boolean enabledAny=false;
            for(int t=0;t<ti.size();t++) {
                boolean enabled=true;
                for(int p=0;p<pi.size();p++)if(marking.get(p)<pre[t][p])enabled=false;
                if(!enabled)continue;
                enabledAny=true;List<Integer> next=new ArrayList<>();
                for(int p=0;p<pi.size();p++)next.add(marking.get(p)-pre[t][p]+post[t][p]);
                next=List.copyOf(next);
                if(!previous.containsKey(next)) {
                    previous.put(next,new Step(marking,transitionNames.get(t)));queue.add(next);
                }
            }
            if(!enabledAny) {
                deadlocks++;
                if(marking.get(pi.get("AttenteA"))+marking.get(pi.get("AttenteB"))!=0)
                    throw new AssertionError("Blocage avec une demande en attente");
            }
        }
        System.out.println("Fichier : "+Path.of(args[0]).getFileName());
        System.out.println("Places="+pi.size()+", transitions="+ti.size()+", marquages accessibles="+previous.size());
        System.out.println("Maximum de jetons par place="+maxToken+", marquages sans transition="+deadlocks);
        System.out.println("Conservation="+conserved+", exclusion="+(bad==null));
        boolean unsafe=args.length>1 && args[1].equals("--expect-unsafe");
        if(unsafe != (bad!=null))throw new AssertionError("Resultat d'exclusion inattendu");
        if(!unsafe && !conserved)throw new AssertionError("Invariant de conservation viole");
        if(bad!=null) {
            List<String> trace=new ArrayList<>();
            for(List<Integer> cursor=bad;previous.get(cursor)!=null;cursor=previous.get(cursor).previous())
                trace.add(previous.get(cursor).transition());
            Collections.reverse(trace);
            System.out.println("Contre-exemple : "+String.join(" -> ",trace));
        }
    }
}
