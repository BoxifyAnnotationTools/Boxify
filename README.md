<h1 align="center">Boxify</h1>
<p align="center"><strong>Local Annotation Tool</strong></p>

<p align="center">
  <img src="assets/boxify.png" width="200" alt="Boxify Icon"/>
</p>

<hr/>

<h2>🚀 Overview</h2>

<h3>What is Boxify?</h3>
<p>
Boxify is a local annotation tool designed to help data annotators label image datasets efficiently.
It is built for users who want a standard annotation workflow that runs offline and supports custom AI models.
</p>

<ul>
  <li>Runs fully locally</li>
  <li>Supports custom-trained models</li>
  <li>Speeds up annotation with automation</li>
  <li>Tes your models directly in your computer</li>
</ul>

<hr/>

<h2>✅ Key Features</h2>

<h3>Core Capabilities</h3>
<ul>
  <li>Fully local (no cloud, full privacy)</li>
  <li>Custom model support (Ultralytics)</li>
  <li>Auto annotation (bbox & polygon)</li>
</ul>

<h3>Productivity</h3>
<ul>
  <li>Fast setup (~10 minutes)</li>
  <li>Smart polygon tools (snapping & refinement)</li>
  <li>Repeat annotation support</li>
</ul>

<h3>Compatibility</h3>
<ul>
  <li>YOLO & Pascal VOC export</li>
  <li>Supports Detection & Segmentation</li>
</ul>

<hr/>

<h2>⚙️ Installation</h2>
<h3>Tkinter and Python must match in version.</h3>
<h4>Linux</h4>
<pre>
chmod +x boxify_linux_installation.bash
./boxify_linux_installation.bash
chmod +x Boxify.desktop
</pre>

<p>Launch by double-clicking the Boxify icon.</p>

<h4>Windows</h4>
<pre>
Run: boxify_windows_installation.bat
</pre>

<p>After installation, double-click the Boxify icon.</p>

<hr/>

<h2>🖥️ Interface</h2>

<p align="center">
  <img src="assets/visualize.png" alt="Boxify UI"/>
</p>
<p align="center">
  <img src="assets/stream.png" alt="Boxify UI"/>
</p>

<hr/>

<h2>⌨️ Controls</h2>

<h3>Navigation</h3>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>A / ←</td><td>Previous image</td></tr>
<tr><td>D / →</td><td>Next image</td></tr>
<tr><td>Delete</td><td>Remove image</td></tr>
</table>

<h3>Annotation Mode</h3>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>M</td><td>Toggle mode</td></tr>
<tr><td>B</td><td>Force bbox mode</td></tr>
<tr><td>F</td><td>Auto annotation</td></tr>
<tr><td>P</td><td>Inference on navigation</td></tr>
</table>

<h3>Drawing & Editing</h3>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>Click</td><td>Add point / select bbox</td></tr>
<tr><td>Double Click / Enter</td><td>Finish polygon</td></tr>
<tr><td>Right Click</td><td>Undo last point</td></tr>
<tr><td>Esc</td><td>Cancel / exit</td></tr>
</table>

<h3>Manage Annotations</h3>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>S</td><td>Change class</td></tr>
<tr><td>R</td><td>Delete annotation</td></tr>
<tr><td>E</td><td>Repeat annotation</td></tr>
</table>

<h3>AI & Training</h3>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>G</td><td>Run inference</td></tr>
<tr><td>T</td><td>Start training (GPU)</td></tr>
</table>

<hr/>

<h2>📁 Project Structure</h2>

<h3>Basic Concept</h3>
<p>You can use your own data as long as the folder structure is correct.</p>
<p>Boxify loads image annotations from XML format. If you want to continue an existing project using Boxify, make sure your images are placed in <code>datasetsInput/{workspace}</code>, the corresponding XML annotations are stored in <code>output/{workspace}</code>, and your model is stored in <code>model/{workspace}</code>.</p>

<pre>
datasetsInput/{workspace}-{index}
output/{workspace}
inference/{workspace}
model/{workspace} => # Only accept .pt model (YOLO Model), renamed as modelAssistant.pt
config/{workspace}.txt
</pre>

<h3>Example (workspace: person)</h3>
<pre>
datasetsInput/person or person-1 (for indexing workspace example)
output/person
inference/person
model/person
config/person.txt
</pre>

<h3>Notes</h3>
<ul>
  <li>Each workspace is isolated</li>
  <li>Supports dataset indexing (-1, -2, etc.)</li>
  <li>XML → output/</li>
  <li>YOLO → inference/</li>
  <li>Models stored per workspace</li>
</ul>

<hr/>

<h2>💾 Annotation Format</h2>

<h3>XML</h3>
<pre>
output/{workspace}/*.xml
</pre>

<pre>
&lt;object&gt;
  &lt;name&gt;vehicle&lt;/name&gt;
  &lt;type&gt;polygon&lt;/type&gt;
  &lt;polygon&gt;
    &lt;point&gt;&lt;x&gt;50&lt;/x&gt;&lt;y&gt;100&lt;/y&gt;&lt;/point&gt;
  &lt;/polygon&gt;
&lt;/object&gt;
</pre>

<h3>YOLO</h3>
<pre>
inference/{workspace}
</pre>

<hr/>

<h2>📤 Export</h2>

<p>Export dataset for YOLOX:</p>
<pre>
python exportTools/export2YOLOX.py
</pre>

<hr/>

<h2>⚠️ Known Issues</h2>

<h3>RuntimeError: ran out of input</h3>

<h4>Causes</h4>
<ul>
  <li>Low VRAM</li>
  <li>Unsupported GPU features</li>
  <li>Memory fragmentation</li>
</ul>

<h4>Solutions</h4>
<ul>
  <li>Reduce image size</li>
  <li>Lower batch size</li>
  <li>Disable AMP</li>
  <li>Use smaller models</li>
  <li>Check dataset integrity</li>
</ul>

<p><strong>Note:</strong> Usually caused by hardware limitations.</p>