Notes:



"alt" way:
Find formation rate
Find average lifespan
Dervive (or hopefully find) an equation relating formation rate and lifespan into a probability

# Questions 

~~- If metallicity and star formation rate are asumed to be constant, why cant one take a smaller sim timeframe (or just the whole sim), and find a formation rate of the target system from that. i.e. out of the million systems 400 are x, so x has a formation rate of ~400/10^5~~

~~- how does one deal with the bias inherited from the intial file? i.e. the distro caused by having S1_mass > S2_mass, the mass distro and upper nad low limits, etc etc. whats the process for taking a simulation, its init settings, and transforming that into a prediction for observed systems. ~~

Turning simulation data into observational predictions depends a lot on what kind of observations you're dealing with. For example, if it's counts in the Milky Way (BH counts, systems counts), you can scale the raw/simulation counts to real counts by scaling them to the Milky Way mass. POSYDON has a key in the population dataframe called "mass_per_metallicity" and one of the columns is "simulated mass" which is the total mass in your POSYDON population. If you take a value from the literature for the total mass in the MW (you can do 6e10 solar masses) and divide that by your POSYDON population simulated mass, you get a count scale (i.e., if the number is 3000 for example, 1 object in your simulation corresponds to 3000 objects in the galaxy). Then, you can weigh your y-axis raw counts by this scaling and get real counts.


- is there a better way for filterting other then where="str bool cond". loading into pandas is obvs very inefficent, but a little easiser to work with


~~- create a notebook to streamline the filtering of a df into specifically the conditions below. Add a check for if S2 is BH and S1 is MS!!!.~~ created a python terminal script

```
df[
    (df['S1_state'] == 'BH') & (df['S2_state'] == 'H-rich_Core_H_burning')
    &  (df['state'] == 'detached')
    &  (df['S2_mass'] < 3) & (df['orbital_period'] < 3.5)
    &  (df['S2_mass'] > .1)
    &  (df['time'] < 10e9)
    ][cols]
```
To-do
- Make hists of distros, graph x prop vs y prop. try and figure out `generalized` formation channels for the system types. Use the `interp_class_HMS_HMS` rows in the oneline to help try and figure out said formation. 
- Maybe just make a python script which takes in the .h5 file and spits out a df with the targeted rows as well as a population file with the formation channels?

- is there a better way for filterting other then where="str bool cond". loading into pandas is obvs very inefficent, but a little easiser to work with 

- ask if I can correct some typos on the POSYDON docs


try some multi-metalticity sims 
add export csv of row before BH collapse 