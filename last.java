import java.util.*;
class java{
    public static void main(String[] args)
    {
        Scanner n=new Scanner(System.in);
        System.out.println("Enter the no of items");
        int kl=n.nextInt();
        System.out.println("Enter the level of risk for each items: ");
        int[] level=new int[kl];
        for(int i=0;i<kl;i++)
        {
            level[i]=n.nextInt();

        }
        Arrays.sort(level);
        for(int i=0;i<kl;i++)
        {
            System.out.print(level[i]);
        }
    }
}